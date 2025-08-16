from pathlib import Path

class AppConfig:
    """应用程序配置常量"""
    # 应用基本信息
    APP_NAME = "PyQt6 Web应用"
    APP_VERSION = "1.0"
    ORGANIZATION_NAME = "PyQt6"
    ORGANIZATION_DOMAIN = "pyqt6.example"
    
    # 网络配置
    DEFAULT_PORT = 8060
    MAX_PORT_ATTEMPTS = 20
    
    # 路径配置
    VUE_DIST_PATH = "vue/dist"
    HTML_ENTRY = "index.html"
    QSS_PATH = "assets/qss/qss.qss"
    ICON_PATH = "assets/icon/qt.ico"
    TRANSLATIONS_PATH = "translations"
    
    # 界面配置
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 600
    SPLASH_WIDTH = 400
    SPLASH_HEIGHT = 200
    
    # 启动进度配置
    SPLASH_PROGRESS_STEPS = [
        ("初始化应用程序...", 0),
        ("加载资源...", 12),
        ("启动服务器...", 24),
        ("初始化Web引擎...", 36),
        ("加载Web页面...", 48),
        ("初始化通信通道...", 60),
        ("准备主窗口...", 72),
        ("即将完成...", 84),
        ("启动完成", 100)
    ]
