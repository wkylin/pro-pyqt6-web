import sys
import logging
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow,QLabel, QLineEdit, QVBoxLayout, QWidget,
                            QSlider,QSpinBox, QTabWidget, QHBoxLayout, QPushButton)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setWindowIcon(QIcon(ResourceManager.get_path("assets/icon/qt.ico")))
        self.setGeometry(200, 200, 900, 600)

        self.label = QLabel("My Name:")
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter you name")

        self.input.textChanged.connect(self.label.setText)

        self.widget = QLabel("Hello")
        self.pixmap = QPixmap(ResourceManager.get_path("assets/img/fx.png"))
        scaled_pixmap = self.pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.widget.setPixmap(scaled_pixmap)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)

        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(100)
        self.spinBox.setValue(50)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        # 添加第一个标签页 - 垂直布局，包含标签和输入框
        tab1 = QWidget()
        layout1 = QVBoxLayout(tab1)
        label1 = QLabel("Enter your name:")
        line_edit1 = QLineEdit()
        layout1.addWidget(label1)
        layout1.addWidget(line_edit1)
        self.tabs.addTab(tab1, "Tab 1")

        # 添加第二个标签页 - 水平布局，包含按钮和滑块
        tab2 = QWidget()
        layout2 = QHBoxLayout(tab2)
        button1 = QPushButton("Click Me")
        slider1 = QSlider(Qt.Orientation.Horizontal)
        slider1.setMinimum(0)
        slider1.setMaximum(100)
        slider1.setValue(50)
        layout2.addWidget(button1)
        layout2.addWidget(slider1)
        self.tabs.addTab(tab2, "Tab 2")

        # 添加第三个标签页 - 网格布局，包含多个标签
        tab3 = QWidget()
        layout3 = QVBoxLayout(tab3)
        for i in range(1, 6):
            label = QLabel(f"Label {i}")
            layout3.addWidget(label)
        self.tabs.addTab(tab3, "Tab 3")

        layout =QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.widget)
        layout.addWidget(self.slider)
        layout.addWidget(self.spinBox)
        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # 应用 QSS 样式表
        self.load_qss()

    def load_qss(self):
        qss_path = ResourceManager.get_path("assets/qss/qss.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                    logger.info("QSS样式表加载成功")
            except Exception as e:
                logger.error(f"QSS加载失败 | 错误: {str(e)}")

app = QApplication(sys.argv)
app.setStyle("Fusion")
window = MainWindow()
window.show()

app.exec()