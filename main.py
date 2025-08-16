import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale, QTranslator, QTimer
from ui.splash_screen import SplashScreen
from ui.main_window import WebBrowserWindow
from config.settings import AppConfig
from utils.resource_manager import ResourceManager
from utils.logger import info, error, Logger

def main():
    """应用程序主入口"""
    # 初始化日志
    Logger()
    info("=" * 50)
    info(f"应用程序启动 | {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
    
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setOrganizationName(AppConfig.ORGANIZATION_NAME)
    app.setOrganizationDomain(AppConfig.ORGANIZATION_DOMAIN)
    app.setStyle("Fusion")
    
    # 加载翻译（如果有）
    translator = QTranslator()
    locale = QLocale.system().name()
    trans_path = ResourceManager.get_path(
        f"{AppConfig.TRANSLATIONS_PATH}/app_{locale}.qm"
    )
    if ResourceManager.exists(trans_path) and translator.load(trans_path):
        app.installTranslator(translator)
        info(f"加载翻译文件: {trans_path}")
    
    # 创建并显示启动画面
    splash = SplashScreen(app)
    app.processEvents()  # 确保启动画面立即显示
    
    # 创建主窗口（但不显示）
    main_window = WebBrowserWindow(splash=splash)
    
    # 连接初始化完成信号
    def on_initialization_complete():
        # 标记启动画面准备关闭
        splash.mark_ready()
        
        # 启动启动画面淡出动画
        splash.start_fade_out()
        
        # 在启动画面淡出动画完成后显示主窗口
        def show_main_window():
            main_window.show_with_animation()
        
        # 使用定时器确保在启动画面完全关闭后再显示主窗口
        QTimer.singleShot(600, show_main_window)
    
    main_window.initialization_complete.connect(on_initialization_complete)
    
    info("应用程序启动完成 | 进入主循环")
    ret = app.exec()
    
    # 彻底清理日志
    info(f"应用程序退出 | 退出代码: {ret}")
    info("=" * 50)
    app.quit()
    sys.exit(ret)

if __name__ == "__main__":
    main()
