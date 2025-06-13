import sys
from PyQt6.QtCore import QUrl, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

class Bridge(QObject):
    # 定义一个信号，用于从JavaScript接收消息
    message_received = pyqtSignal(str)

    @pyqtSlot(str)
    def send_to_python(self, message):
        """接收来自JavaScript的消息"""
        self.message_received.emit(message)

    def send_to_javascript(self, web_view, message):
        """向JavaScript发送消息"""
        web_view.page().runJavaScript(f"""
            // 检查消息处理函数是否存在
            if (window.handlePythonMessage) {{
                window.handlePythonMessage("{message}");
            }}
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建主窗口部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建WebEngineView
        self.web_view = QWebEngineView()

        # 创建用于显示从JavaScript接收的消息的文本框
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)

        # 创建用于发送消息到JavaScript的输入框和按钮
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(50)
        self.send_button = QPushButton("发送到JavaScript")
        self.send_button.clicked.connect(self.send_message)

        # 添加部件到布局
        self.layout.addWidget(self.web_view)
        self.layout.addWidget(self.message_display)
        self.layout.addWidget(self.message_input)
        self.layout.addWidget(self.send_button)

        # 设置窗口属性
        self.setWindowTitle("PyQt6与JavaScript双向通信示例")
        self.resize(800, 600)

        # 创建桥接对象
        self.bridge = Bridge()
        self.bridge.message_received.connect(self.on_message_received)

        # 设置WebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # 加载本地HTML文件（这里使用一个包含JavaScript桥接代码的HTML）
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>PyQt6与JavaScript通信示例</title>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
                // 等待WebChannel初始化
                var bridge;
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    bridge = channel.objects.bridge;

                    // 向Python发送消息
                    bridge.send_to_python("JavaScript已加载并准备就绪");

                    // 为按钮添加点击事件，向Python发送消息
                    document.getElementById('sendToPython').addEventListener('click', function() {
                        var message = document.getElementById('messageInput').value;
                        bridge.send_to_python(message);
                    });
                });

                // 定义一个函数，用于接收来自Python的消息
                window.handlePythonMessage = function(message) {
                    var logElement = document.getElementById('messageLog');
                    var newMessage = document.createElement('div');
                    newMessage.textContent = '来自Python: ' + message;
                    logElement.appendChild(newMessage);
                };
            </script>
        </head>
        <body>
            <h1>PyQt6与JavaScript通信示例</h1>

            <div>
                <input type="text" id="messageInput" placeholder="输入消息...">
                <button id="sendToPython">发送到Python</button>
            </div>

            <h3>消息日志:</h3>
            <div id="messageLog"></div>
        </body>
        </html>
        """

        # 加载HTML内容
        self.web_view.setHtml(html_content)

    def send_message(self):
        """发送消息到JavaScript"""
        message = self.message_input.toPlainText()
        if message:
            self.bridge.send_to_javascript(self.web_view, message)
            self.message_input.clear()

    def on_message_received(self, message):
        """处理从JavaScript接收的消息"""
        self.message_display.append(f"收到来自JavaScript的消息: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
