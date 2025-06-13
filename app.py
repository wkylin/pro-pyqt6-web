import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow,QLabel, QLineEdit, QVBoxLayout, QWidget,
                            QSlider,QSpinBox, QTabWidget, QHBoxLayout, QPushButton)


def load_qss_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading QSS file: {e}")
        return ""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setWindowIcon(QIcon("assets/icon/icon.png"))
        self.setGeometry(200, 200, 900, 600)

        self.label = QLabel("My Name:")
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter you name")

        self.input.textChanged.connect(self.label.setText)

        self.widget = QLabel("Hello")
        self.pixmap = QPixmap("assets/img/fx.png")
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
        qss_path = "assets/qss/qss.qss"
        qss_content = load_qss_file(qss_path)
        if qss_content:
            self.setStyleSheet(qss_content)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()