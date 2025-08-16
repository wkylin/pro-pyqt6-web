import os
import time
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMessageBox, QPushButton, QApplication)
from PyQt6.QtCore import (QUrl, Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QThread)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from config.settings import AppConfig
from core.bridge import Bridge
from core.server import HTTPServerManager
from utils.resource_manager import ResourceManager
from utils.port_manager import PortManager
from utils.logger import info, error, debug

class WebBrowserWindow(QMainWindow):
    """应用程序主窗口"""
    
    # 信号定义
    initialization_complete = pyqtSignal()
    
    def __init__(self, splash=None):
        super().__init__()
        self.original_port = AppConfig.DEFAULT_PORT
        self.html_path = os.path.join(AppConfig.VUE_DIST_PATH, AppConfig.HTML_ENTRY)
        self.server_manager: HTTPServerManager = None
        self.web_view: QWebEngineView = None
        self.bridge: Bridge = None
        self.final_port: int = None
        self.is_closing = False  # 标记是否正在关闭
        self.splash = splash  # 启动画面引用
        
        # 设置窗口初始透明度（用于淡入效果）
        self.setWindowOpacity(0.0)
        
        # 更新启动画面状态
        if self.splash:
            self.splash.set_status("正在初始化UI...")
        
        self.init_ui()
        self.load_qss()
        self.setup_server()
        
        info("主窗口初始化完成")
    
    def init_ui(self) -> None:
        """初始化用户界面"""
        self.setWindowTitle(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.setGeometry(
            100, 100, 
            AppConfig.WINDOW_WIDTH, 
            AppConfig.WINDOW_HEIGHT
        )
        
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
        if ResourceManager.exists(AppConfig.ICON_PATH):
            self.setWindowIcon(ResourceManager.load_icon(AppConfig.ICON_PATH))
    
    def load_qss(self) -> None:
        """加载QSS样式表"""
        if ResourceManager.exists(AppConfig.QSS_PATH):
            try:
                qss_content = ResourceManager.load_text(AppConfig.QSS_PATH)
                self.setStyleSheet(qss_content)
                info("QSS样式表加载成功")
            except Exception as e:
                error(f"QSS加载失败: {str(e)}")
    
    def setup_server(self) -> None:
        """设置并启动HTTP服务器"""
        # 更新启动画面状态
        if self.splash:
            self.splash.set_status("正在启动服务器...")
        
        vue_dir = ResourceManager.get_path(AppConfig.VUE_DIST_PATH)
        if not os.path.exists(vue_dir):
            QMessageBox.critical(
                self, "启动错误", 
                f"无法找到Vue项目目录:\n{vue_dir}"
            )
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
    
    def on_server_started(self, port: int) -> None:
        """服务器启动成功后加载HTML"""
        info(f"服务器启动完成 | 端口: {port}")
        
        # 更新启动画面状态
        if self.splash:
            self.splash.set_status("正在加载Web页面...")
        
        self.load_html()
    
    def on_server_failed(self, error_msg: str, details: dict) -> None:
        """服务器启动失败处理"""
        error(f"服务器启动失败详情: {details}")
        QMessageBox.critical(
            self, "服务器启动失败", 
            f"启动HTTP服务器时发生错误:\n{error_msg}"
        )
        self.close()
    
    def load_html(self) -> None:
        """加载目标HTML页面"""
        html_file = os.path.basename(self.html_path)
        url = QUrl(f"http://localhost:{self.final_port}/{html_file}#/")
        info(f"加载页面 | URL: {url.toString()}")
        self.web_view.load(url)
        self.web_view.page().loadFinished.connect(self.on_page_load_finished)
    
    def on_page_load_finished(self, success: bool) -> None:
        """页面加载完成回调"""
        if success:
            info("Web页面加载完成，初始化通信通道")
            
            # 更新启动画面状态
            if self.splash:
                self.splash.set_status("正在初始化通信通道...")
            
            self.init_web_channel()
            self.add_calculator_button()
            
            # 更新启动画面状态
            if self.splash:
                self.splash.set_status("正在准备主窗口...")
            
            # 标记初始化完成
            self.initialization_complete.emit()
        else:
            error("Web页面加载失败")
            QMessageBox.warning(
                self, "页面加载警告", 
                "Web页面加载失败，请检查资源路径"
            )
    
    def init_web_channel(self) -> None:
        """初始化WebChannel通信"""
        try:
            self.bridge = Bridge()
            self.bridge.setup_channel(self.web_view.page())
            
            # 连接信号示例
            self.bridge.messageFromQt.connect(self.on_bridge_message)
            
            # 发送初始化消息
            self.bridge.send_message_to_web("Qt应用已启动，通信通道已建立")
            info("WebChannel初始化成功")
        except Exception as e:
            error(f"WebChannel初始化失败: {str(e)}")
            QMessageBox.error(
                self, "通信初始化失败", 
                f"Qt与Web页面通信失败:\n{str(e)}"
            )
    
    def add_calculator_button(self) -> None:
        """添加计算按钮"""
        calculator_button = QPushButton("执行计算 (55 + 3)")
        calculator_button.clicked.connect(self.execute_calculation)
        self.main_layout.addWidget(calculator_button)
    
    def execute_calculation(self) -> None:
        """执行JavaScript计算"""
        if not self.web_view:
            return
            
        self.web_view.page().runJavaScript("""
            if (window.webCalculator && typeof window.webCalculator.performCalculation === 'function') {
                webCalculator.performCalculation(55, 3)
                    .then(result => {
                        if (window.bridge && typeof window.bridge.receiveCalculationResult === 'function') {
                            window.bridge.receiveCalculationResult(result);
                        }
                    })
                    .catch(error => console.error('计算失败:', error));
            } else {
                console.error('webCalculator未定义或performCalculation方法不存在');
            }
        """)
    
    def on_bridge_message(self, message: str) -> None:
        """处理桥接器发来的消息"""
        debug(f"桥接器消息: {message}")
    
    def show_with_animation(self) -> None:
        """带动画显示主窗口"""
        # 创建淡入动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 显示窗口并启动动画
        self.show()
        self.fade_in_animation.start()
    
    def closeEvent(self, event) -> None:
        """重写关闭事件，优化退出速度"""
        if self.is_closing:
            event.accept()
            return
            
        self.is_closing = True
        info("开始关闭应用程序，释放资源...")
        start_time = time.time()
        
        try:
            # 1. 优先停止服务器
            if self.server_manager:
                debug("停止HTTP服务器")
                self.server_manager.stop()
                self.server_manager = None
            
            # 2. 停止页面加载和JavaScript活动
            if self.web_view:
                debug("停止Web页面活动")
                self.web_view.stop()  # 停止加载
                self.web_view.load(QUrl("about:blank"))  # 加载空白页清除状态
                self.web_view.page().loadFinished.disconnect()
                QApplication.processEvents()  # 处理事件循环
            
            # 3. 清理WebEngine资源
            if self.web_view:
                debug("清理WebEngine资源")
                # 清除缓存和访问记录
                profile = self.web_view.page().profile()
                profile.clearHttpCache()
                profile.clearAllVisitedLinks()
                
                # 安全删除WebView
                self.web_view.setPage(None)
                self.web_view.deleteLater()
                self.web_view = None
            
            # 4. 清理通信桥接
            if self.bridge:
                self.bridge.deleteLater()
                self.bridge = None
            
            info(f"资源释放完成 | 总耗时: {time.time() - start_time:.3f}s")
            event.accept()
            
        except Exception as e:
            error(f"关闭过程中发生错误: {str(e)}", exc_info=True)
            event.accept()
