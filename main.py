import sys
import os
import socket
import logging
import time
import threading
import http.server
import socketserver
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                            QPushButton, QSplashScreen, QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineSettings, 
                                  QWebEnginePage, 
                                  QWebEngineProfile)
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import (QUrl, Qt, QThread, pyqtSignal, QObject,
                         QT_VERSION_STR, PYQT_VERSION_STR, QTranslator, QLocale, pyqtSlot)

# ------------------------------
# 日志配置
# ------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PyQt6Browser")


# ------------------------------
# 工具类：资源管理
# ------------------------------
class ResourceManager:
    @staticmethod
    def get_path(relative_path):
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)

    @staticmethod
    def load_png_as_pixmap(png_path, width=600, height=400):
        pixmap_path = ResourceManager.get_path(png_path)
        if not os.path.exists(pixmap_path):
            logger.warning(f"PNG文件不存在 | 路径: {pixmap_path}")
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.gray)
            return pixmap

        try:
            pixmap = QPixmap(pixmap_path)
            return pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        except Exception as e:
            logger.error(f"加载PNG失败 | 路径: {pixmap_path}, 错误: {str(e)}")
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.gray)
            return pixmap


# ------------------------------
# 工具类：端口管理
# ------------------------------
class PortManager:
    @staticmethod
    def is_port_available(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) != 0
        except Exception as e:
            logger.error(f"端口检查失败 | 端口: {port}, 错误: {str(e)}")
            return False

    @staticmethod
    def find_available_port(start_port=8060, max_attempts=20):
        for port in range(start_port, start_port + max_attempts):
            if PortManager.is_port_available(port):
                logger.info(f"找到可用端口 | 端口: {port}")
                return port
        logger.error(f"端口查找失败 | 尝试范围: {start_port}-{start_port + max_attempts - 1}")
        return None


# ------------------------------
# 服务器相关类
# ------------------------------
class ServerSignals(QObject):
    started = pyqtSignal(int)
    failed = pyqtSignal(str, dict)


class SilentHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """静默模式的HTTP处理器，不输出访问日志"""
    def log_message(self, format, *args):
        pass


class HTTPServerManager:
    """HTTP服务器管理器，优化退出速度"""
    def __init__(self, port, directory):
        self.port = port
        self.directory = directory
        self.server = None
        self.thread = None
        self.running = False
        self.signals = ServerSignals()
        self.wakeup_socket = None  # 用于唤醒阻塞的服务器

    def start(self):
        """启动服务器线程"""
        self.running = True
        # 创建唤醒套接字对
        self.wakeup_socket = socket.socketpair()
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        """服务器运行逻辑"""
        try:
            if not os.path.exists(self.directory):
                raise FileNotFoundError(f"服务目录不存在: {self.directory}")
            
            os.chdir(self.directory)
            # 创建服务器
            self.server = socketserver.ThreadingTCPServer(
                ("", self.port), 
                SilentHTTPHandler
            )
            # 设置地址复用
            self.server.allow_reuse_address = True
            self.server.timeout = 0.1  # 缩短超时时间，加快响应停止信号
            self.signals.started.emit(self.port)
            logger.info(f"HTTP服务器启动 | 端口: {self.port}, 目录: {self.directory}")

            # 循环处理请求，直到收到停止信号
            while self.running:
                # 使用select同时监听服务器和唤醒套接字
                readable, _, _ = select.select(
                    [self.server.socket, self.wakeup_socket[0]],
                    [], [], self.server.timeout
                )
                if readable:
                    if self.wakeup_socket[0] in readable:
                        # 读取唤醒信号
                        self.wakeup_socket[0].recv(1)
                        break  # 退出循环
                    elif self.server.socket in readable:
                        self.server.handle_request()  # 处理HTTP请求

        except Exception as e:
            error_details = {
                "exception": str(e),
                "directory": self.directory,
                "port": self.port,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.error(f"服务器启动失败: {str(e)}", exc_info=True)
            self.signals.failed.emit(str(e), error_details)

        finally:
            self._cleanup_server()
            self.running = False
            logger.info("HTTP服务器线程退出")

    def _cleanup_server(self):
        """清理服务器资源"""
        # 关闭唤醒套接字
        if self.wakeup_socket:
            try:
                self.wakeup_socket[0].close()
                self.wakeup_socket[1].close()
            except Exception as e:
                logger.error(f"唤醒套接字清理失败: {str(e)}")
            self.wakeup_socket = None

        # 清理服务器
        if self.server:
            try:
                if hasattr(self.server, 'socket'):
                    self.server.socket.close()
                self.server.server_close()
            except Exception as e:
                logger.error(f"服务器清理失败: {str(e)}")
            self.server = None

    def stop(self):
        """停止服务器 - 优化版本"""
        if not self.running:
            return
            
        self.running = False
        
        # 发送唤醒信号，立即中断服务器的select阻塞
        if self.wakeup_socket:
            try:
                self.wakeup_socket[1].send(b'1')  # 发送一个字节唤醒服务器
            except Exception as e:
                logger.warning(f"发送唤醒信号失败: {str(e)}")
        
        # 等待线程终止（缩短等待时间）
        if self.thread and self.thread.is_alive():
            self.thread.join(0.5)  # 最多等待500ms
            if self.thread.is_alive():
                logger.warning("HTTP服务器线程未能正常终止")


# ------------------------------
# Web与Qt通信桥梁
# ------------------------------
class Bridge(QObject):
    messageFromQt = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.web_message_count = 0

    @pyqtSlot(str)
    def processWebMessage(self, message):
        self.web_message_count += 1
        info = f"收到Web消息 | 编号: {self.web_message_count}, 内容: {message[:50]}..."
        logger.debug(info)
        self.messageFromQt.emit(info)

    @pyqtSlot(result=str)
    def getQtVersion(self):
        return f"PyQt6 版本: {PYQT_VERSION_STR}, QT6版本: {QT_VERSION_STR}"

    @pyqtSlot(int, int, result=int)
    def calculateSum(self, a, b):
        return a + b

    @pyqtSlot(int)
    def receiveCalculationResult(self, result):
        print("计算结果:", result)


# ------------------------------
# 主窗口类
# ------------------------------
class WebBrowserWindow(QMainWindow):
    def __init__(self, port=8060, html_path="vue/dist/index.html"):
        super().__init__()
        self.original_port = port
        self.html_path = html_path
        self.server_manager = None
        self.web_view = None
        self.bridge = None
        self.channel = None
        self.final_port = None
        self.is_closing = False  # 标记是否正在关闭

        self.init_ui()
        self.load_qss()
        self.setup_server()

    def init_ui(self):
        self.setWindowTitle("PyQt6 WebEngine 应用")
        self.setGeometry(100, 100, 900, 600)
        
        # 主布局
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)
        
        # 初始化WebView
        self.web_view = QWebEngineView()
        self.main_layout.addWidget(self.web_view)
        
        # 配置Web设置
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # 设置窗口图标
        icon_path = ResourceManager.get_path("assets/icon/qt.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def load_qss(self):
        qss_path = ResourceManager.get_path("assets/qss/qss.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                    logger.info("QSS样式表加载成功")
            except Exception as e:
                logger.error(f"QSS加载失败: {str(e)}")

    def setup_server(self):
        """设置并启动HTTP服务器"""
        vue_dir = os.path.dirname(ResourceManager.get_path(self.html_path))
        if not os.path.exists(vue_dir):
            QMessageBox.critical(self, "启动错误", f"无法找到Vue项目目录:\n{vue_dir}")
            self.close()
            return

        self.final_port = PortManager.find_available_port(self.original_port)
        if not self.final_port:
            QMessageBox.critical(self, "启动错误", "无法找到可用端口")
            self.close()
            return

        # 初始化服务器管理器
        self.server_manager = HTTPServerManager(self.final_port, vue_dir)
        self.server_manager.signals.started.connect(self.on_server_started)
        self.server_manager.signals.failed.connect(self.on_server_failed)
        self.server_manager.start()

    def on_server_started(self, port):
        """服务器启动成功后加载HTML"""
        logger.info(f"服务器启动完成 | 端口: {port}")
        self.load_html()

    def on_server_failed(self, error_msg, details):
        """服务器启动失败处理"""
        logger.error(f"服务器启动失败详情: {details}")
        QMessageBox.critical(self, "服务器启动失败", f"启动HTTP服务器时发生错误:\n{error_msg}")
        self.close()

    def load_html(self):
        """加载目标HTML页面"""
        html_file = os.path.basename(self.html_path)
        url = QUrl(f"http://localhost:{self.final_port}/{html_file}#/")
        logger.info(f"加载页面 | URL: {url.toString()}")
        self.web_view.load(url)
        self.web_view.page().loadFinished.connect(self.on_page_load_finished)

    def on_page_load_finished(self, success):
        """页面加载完成回调"""
        if success:
            logger.info("Web页面加载完成，初始化通信通道")
            self.init_web_channel()
            self.add_calculator_button()
        else:
            logger.warning("Web页面加载失败")
            QMessageBox.warning(self, "页面加载警告", "Web页面加载失败，请检查资源路径")

    def init_web_channel(self):
        """初始化WebChannel通信"""
        try:
            self.bridge = Bridge()
            self.channel = QWebChannel()
            self.channel.registerObject("bridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)
            logger.info("WebChannel初始化成功")
        except Exception as e:
            logger.error(f"WebChannel初始化失败: {str(e)}")
            QMessageBox.error(self, "通信初始化失败", f"Qt与Web页面通信失败:\n{str(e)}")

    def add_calculator_button(self):
        """添加计算按钮"""
        calculator_button = QPushButton("执行计算")
        calculator_button.clicked.connect(self.execute_calculation)
        self.main_layout.addWidget(calculator_button)

    def execute_calculation(self):
        """执行JavaScript计算"""
        self.web_view.page().runJavaScript("""
            webCalculator.performCalculation(55, 3)
                .then(result => window.bridge.receiveCalculationResult(result))
        """)

    def closeEvent(self, event):
        """重写关闭事件，优化退出速度"""
        if self.is_closing:
            event.accept()
            return

        self.is_closing = True
        logger.info("开始关闭应用程序，释放资源...")
        start_time = time.time()

        try:
            # 1. 优先停止服务器，减少等待时间
            if self.server_manager:
                logger.debug("立即停止HTTP服务器")
                self.server_manager.stop()
                self.server_manager = None

            # 2. 停止页面加载和JavaScript活动
            if self.web_view:
                logger.debug("停止Web页面活动")
                self.web_view.stop()  # 停止加载
                self.web_view.load(QUrl("about:blank"))  # 加载空白页清除状态
                QApplication.processEvents()  # 处理事件循环

            # 3. 断开所有信号连接
            if self.web_view and self.web_view.page():
                try:
                    self.web_view.page().loadFinished.disconnect()
                except Exception as e:
                    logger.warning(f"断开页面加载信号时出错: {str(e)}")

            # 4. 清理WebEngine资源
            if self.web_view:
                logger.debug("清理WebEngine资源")
                # 清除缓存和访问记录
                profile = self.web_view.page().profile()
                profile.clearHttpCache()
                profile.clearAllVisitedLinks()
                
                # 安全删除WebView
                self.web_view.setPage(None)
                self.web_view.deleteLater()
                self.web_view = None

            # 5. 清理WebChannel和Bridge
            if self.channel:
                if self.bridge:
                    self.channel.deregisterObject(self.bridge)
                self.channel = None

            if self.bridge:
                self.bridge.deleteLater()
                self.bridge = None

            logger.info(f"资源释放完成 | 总耗时: {time.time() - start_time:.3f}s")
            event.accept()

        except Exception as e:
            logger.error(f"关闭过程中发生错误: {str(e)}", exc_info=True)
            event.accept()


# ------------------------------
# 主函数
# ------------------------------
def main():
    # 导入select模块（用于服务器唤醒机制）
    global select
    import select
    
    logger.info("应用程序启动 | 开始初始化")
    app = QApplication(sys.argv)
    app.setApplicationName("PyQt6 Web应用")
    app.setStyle("Fusion")

    # 加载翻译（如果有）
    translator = QTranslator()
    locale = QLocale.system().name()
    trans_path = ResourceManager.get_path(f"translations/app_{locale}.qm")
    if os.path.exists(trans_path) and translator.load(trans_path):
        app.installTranslator(translator)

    # 启动画面
    # splash_pixmap = ResourceManager.load_png_as_pixmap("assets/splash/splash.png", 100, 100)
    # splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    # splash.show()
    # app.processEvents()

    # 显示主窗口
    main_window = WebBrowserWindow()
    main_window.show()
    # splash.finish(main_window)

    logger.info("应用程序启动完成 | 进入主循环")
    ret = app.exec()
    
    # 彻底清理日志
    logging.shutdown()
    sys.exit(ret)


if __name__ == "__main__":
    main()
    