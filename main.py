import sys
import os
import threading
import http.server
import socketserver
import socket
import logging
import time
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                            QPushButton, QSplashScreen, QMessageBox, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import (QUrl, Qt, QThread, pyqtSignal, QObject,
                            QT_VERSION_STR, QTranslator, QLocale, QLibraryInfo, pyqtSlot)

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PyQt6Browser")

class ResourceManager:
    """资源管理类，处理不同环境下的资源路径"""
    @staticmethod
    def get_path(relative_path):
        base_path = os.path.abspath(os.path.dirname(__file__))
        logger.debug(f"资源路径解析 | 基础路径: {base_path}, 相对路径: {relative_path}")
        return os.path.join(base_path, relative_path)

    @staticmethod
    def load_png_as_pixmap(png_path, width=600, height=400):
        pixmap_path = ResourceManager.get_path(png_path)
        if os.path.exists(pixmap_path):
            try:
                pixmap = QPixmap(pixmap_path)
                return pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            except Exception as e:
                logger.error(f"加载PNG失败 | 路径: {pixmap_path}, 错误: {str(e)}")
        logger.warning(f"PNG文件不存在 | 路径: {pixmap_path}")
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.gray)
        return pixmap

class PortManager:
    """端口管理类"""
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

class ServerSignals(QObject):
    started = pyqtSignal(int)
    failed = pyqtSignal(str, dict)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        """
        This method is intentionally left empty to suppress log messages from the HTTP server.
        The default implementation logs every request, which can be noisy and unnecessary for this application.
        """
        pass

class HTTPServerThread(QThread):
    def __init__(self, port=8060, directory="."):
        super().__init__()
        self.port = port
        self.directory = directory
        self.signals = ServerSignals()
        self.httpd = None
        self.running = False
        self._stop_event = threading.Event()

    def run(self):
        try:
            if not os.path.exists(self.directory):
                raise FileNotFoundError(f"服务目录不存在 | 路径: {self.directory}")
            os.chdir(self.directory)
            logger.info(f"服务器工作目录 | 路径: {os.getcwd()}")
            self.httpd = socketserver.ThreadingTCPServer(("", self.port), CustomHandler)
            self.httpd.allow_reuse_address = True
            logger.info(f"服务器启动成功 | 端口: {self.port}")
            self.signals.started.emit(self.port)
            self.running = True
            self.httpd.serve_forever()
        except Exception as e:
            error_details = {
                "exception": str(e),
                "directory": self.directory,
                "port": self.port,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.error(f"服务器启动失败 | 错误: {str(e)}", exc_info=True)
            self.signals.failed.emit(str(e), error_details)
        finally:
            self.running = False

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self._stop_event.set()
        self.wait(1000)
        self.running = False
        logger.info("服务器已关闭")

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
        return f"PyQt6 版本: {QT_VERSION_STR}"

    @pyqtSlot(int, int, result=int)
    def calculateSum(self, a, b):
        logger.info(f"Sum: {a + b}")
        return a + b
    @pyqtSlot(int)
    def receiveCalculationResult(self, result):
        print("计算结果:", result)

class WebBrowserWindow(QMainWindow):
    def __init__(self, port=8060, html_path="vue/dist/index.html"):
        super().__init__()
        self.original_port = port
        self.html_path = html_path
        self.server_thread = None
        self.bridge = None
        self.channel = None
        self.final_port = None
        self.init_ui()
        self.load_qss()
        self.setup_server()

    def init_ui(self):
        self.setWindowTitle("PyQt6 WebEngine 应用")
        icon_path = ResourceManager.get_path("assets/icon/qt.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 900, 600)
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setCentralWidget(central_widget)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

    def load_qss(self):
        qss_path = ResourceManager.get_path("assets/qss/qss.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                    logger.info("QSS样式表加载成功")
            except Exception as e:
                logger.error(f"QSS加载失败 | 错误: {str(e)}")

    def setup_server(self):
        vue_dir = os.path.dirname(ResourceManager.get_path(self.html_path))
        if not os.path.exists(vue_dir):
            logger.error(f"Vue目录不存在 | 路径: {vue_dir}")
            QMessageBox.critical(self, "启动错误", f"无法找到Vue项目目录:\n{vue_dir}")
            self.close()
            return
        self.final_port = PortManager.find_available_port(self.original_port)
        if not self.final_port:
            QMessageBox.critical(self, "启动错误", "无法找到可用端口")
            self.close()
            return
        self.server_thread = HTTPServerThread(self.final_port, vue_dir)
        self.server_thread.signals.started.connect(self.on_server_started)
        self.server_thread.signals.failed.connect(self.on_server_failed)
        self.server_thread.start()

    def on_server_started(self, port):
        logger.info(f"服务器启动完成 | 端口: {port}")
        self.load_html()

    def on_server_failed(self, error_msg, details):
        logger.error(f"服务器启动失败详情 | {details}")
        QMessageBox.critical(self, "服务器启动失败", f"启动HTTP服务器时发生错误:\n{error_msg}")
        self.close()

    def load_html(self):
        html_file = os.path.basename(self.html_path)
        url = QUrl(f"http://localhost:{self.final_port}/{html_file}#/")
        logger.info(f"加载页面 | URL: {url.toString()}")
        self.web_view.load(url)
        self.web_view.page().loadFinished.connect(self.on_page_load_finished)

    def on_page_load_finished(self, success):
        if success:
            logger.info("Web页面加载完成 | 初始化通信通道")
            self.init_web_channel()
            self.add_calculator_button()
        else:
            logger.warning("Web页面加载失败 | 可能是网络或资源问题")
            QMessageBox.warning(self, "页面加载警告", "Web页面加载失败，请检查资源路径")

    def init_web_channel(self):
        try:
            self.bridge = Bridge()
            self.channel = QWebChannel()
            self.channel.registerObject("bridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)
            logger.info("WebChannel初始化成功")
            test_msg = f"通信测试 | PyQt版本: {QT_VERSION_STR}"
            self.bridge.messageFromQt.emit(test_msg)
        except Exception as e:
            logger.error(f"WebChannel初始化失败 | 错误: {str(e)}")
            QMessageBox.error(self, "通信初始化失败", f"Qt与Web页面通信失败:\n{str(e)}")

    def add_calculator_button(self):
        calculator_button = QPushButton("执行计算")
        calculator_button.clicked.connect(self.execute_calculation)
        layout = self.centralWidget().layout()
        layout.addWidget(calculator_button)

    def execute_calculation(self):
        self.web_view.page().runJavaScript("webCalculator.performCalculation(55, 3).then(result => {window.bridge.receiveCalculationResult(result)});")

    def js_callback(self, result):
        # 回调函数，处理 JavaScript 执行结果
        print("JavaScript result:", result)

    def closeEvent(self, event):
        logger.info("应用程序关闭事件 | 开始释放资源")
        if self.server_thread and self.server_thread.isRunning():
            self.server_thread.stop()
            self.server_thread.wait()
        event.accept()

def main():
    logger.info("应用程序启动 | 开始初始化")
    app = QApplication(sys.argv)
    app.setApplicationName("PyQt6 Web应用")
    translator = QTranslator()
    locale = QLocale.system().name()
    trans_path = ResourceManager.get_path(f"translations/app_{locale}.qm")
    if os.path.exists(trans_path) and translator.load(trans_path):
        app.installTranslator(translator)
    splash_pixmap = ResourceManager.load_png_as_pixmap("assets/splash/splash.png", 100, 100)
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    main_window = WebBrowserWindow()
    main_window.show()
    splash.finish(main_window)
    logger.info("应用程序启动完成 | 进入主循环")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()