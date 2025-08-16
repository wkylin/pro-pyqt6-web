from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QLabel, QProgressBar, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap
from utils.logger import info, debug
from config.settings import AppConfig

class SplashScreen(QSplashScreen):
    """应用程序启动画面，确保能正常显示"""
    
    def __init__(self, app):
        # 关键修复1：设置初始空白pixmap，确保窗口有实体
        blank_pixmap = QPixmap(AppConfig.SPLASH_WIDTH, AppConfig.SPLASH_HEIGHT)
        blank_pixmap.fill(Qt.GlobalColor.transparent)  # 透明背景，后续由样式表控制
        super().__init__(blank_pixmap)
        
        self.app = app
        self.progress = 0
        self.is_ready = False
        
        # 设置启动画面属性（确保窗口可见）
        self.setFixedSize(AppConfig.SPLASH_WIDTH, AppConfig.SPLASH_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen 
            | Qt.WindowType.FramelessWindowHint 
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)  # 显示时不抢夺焦点
        
        # 创建中心部件并设置布局（关键修复2：确保布局正确挂载）
        container = QWidget(self)
        container.setGeometry(0, 0, AppConfig.SPLASH_WIDTH, AppConfig.SPLASH_HEIGHT)
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        container.setLayout(self.layout)  # 显式设置布局，确保生效
        
        # 添加标题标签（确保有可见内容）
        self.title_label = QLabel(AppConfig.APP_NAME)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(self.title_label)
        
        # 状态标签
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #e0e0e0;")
        self.layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        self.layout.addWidget(self.progress_bar)
        
        # 版本标签
        self.version_label = QLabel(f"版本 {AppConfig.APP_VERSION}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("font-size: 10px; color: #a0a0a0;")
        self.layout.addWidget(self.version_label)
        
        # 样式表（关键修复3：确保背景可见）
        self.setStyleSheet("""
            QSplashScreen {
                background-color: #2D2D30;  /* 明确背景色，避免透明 */
                border-radius: 10px;
                border: 1px solid #444;  /* 边框，增强可见性 */
            }
        """)
        
        # 居中显示
        screen = app.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2, 
            (screen.height() - self.height()) // 2
        )
        
        # 启动定时器更新进度
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)
        
        # 状态消息和进度阈值
        self.status_messages = [
            "正在初始化应用程序...",
            "正在加载资源...",
            "正在启动服务器...",
            "正在初始化Web引擎...",
            "正在加载Web页面...",
            "正在初始化通信通道...",
            "正在准备主窗口...",
            "即将完成..."
        ]
        self.status_thresholds = [0, 12, 24, 36, 48, 60, 72, 84, 100]
        self.current_status_index = 0
        self.last_progress = -1
        
        # 淡出动画
        self.fade_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.finished.connect(self.close)
        
        # 关键修复4：显式调用show，并立即处理事件
        self.show()
        app.processEvents()  # 强制刷新，确保窗口显示
        info("启动画面初始化完成并显示")
    
    def update_progress(self):
        """更新进度条和状态消息"""
        if self.is_ready:
            self.progress = min(100, self.progress + 5)
        else:
            self.progress += 1
        
        if self.progress > 100:
            self.progress = 100
        
        self.progress_bar.setValue(self.progress)
        
        if self.progress != self.last_progress:
            self.last_progress = self.progress
            
            # 更新状态消息
            target_status_index = 0
            for i in range(len(self.status_thresholds) - 1):
                if self.progress >= self.status_thresholds[i] and self.progress < self.status_thresholds[i + 1]:
                    target_status_index = i
                    break
            
            if target_status_index != self.current_status_index:
                self.current_status_index = target_status_index
                self.status_label.setText(self.status_messages[target_status_index])
        
        self.app.processEvents()  # 及时刷新界面
    
    def set_status(self, message):
        """设置状态消息"""
        self.status_label.setText(message)
        self.app.processEvents()
    
    def mark_ready(self):
        """标记准备完成"""
        self.is_ready = True
        self.status_label.setText("所有任务完成，正在启动主窗口...")
    
    def start_fade_out(self):
        """启动淡出动画"""
        self.timer.stop()
        self.fade_animation.start()
