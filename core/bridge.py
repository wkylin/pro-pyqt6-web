from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage 
from config.settings import AppConfig
from utils.logger import info, debug

class Bridge(QObject):
    """Qt与Web页面通信的桥接类"""
    
    # 信号定义 - 发送消息到Web页面
    messageFromQt = pyqtSignal(str)
    jsonFromQt = pyqtSignal(dict)
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.web_message_count = 0
        self.channel = QWebChannel(self)
        self.channel.registerObject("bridge", self)
    
    def setup_channel(self, page: QWebEnginePage) -> None:
        """设置WebChannel到指定页面"""
        page.setWebChannel(self.channel)
        info("WebChannel已绑定到页面")
    
    @pyqtSlot(str)
    def processWebMessage(self, message: str) -> None:
        """处理来自Web页面的字符串消息"""
        self.web_message_count += 1
        info(f"收到Web消息 | 编号: {self.web_message_count}, 内容: {message}...")
        self.messageFromQt.emit(f"已收到消息: {message}...")
    
    @pyqtSlot(dict)
    def processWebJson(self, data: dict) -> None:
        """处理来自Web页面的JSON数据"""
        self.web_message_count += 1
        info(f"收到Web JSON数据 | 编号: {self.web_message_count}")
        debug(f"JSON内容: {data}")
        
        # 处理后返回响应
        response = {
            "status": "success",
            "received": True,
            "message": "数据已收到",
            "data": {
                "original_size": len(str(data)),
                "timestamp": self._get_timestamp()
            }
        }
        self.jsonFromQt.emit(response)
    
    @pyqtSlot(result=str)
    def getQtVersion(self) -> str:
        """获取Qt版本信息"""
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        return f"PyQt6 版本: {PYQT_VERSION_STR}, Qt 版本: {QT_VERSION_STR}"
    
    @pyqtSlot(int, int, result=int)
    def calculateSum(self, a: int, b: int) -> int:
        """计算两个数的和"""
        result = a + b
        debug(f"计算 {a} + {b} = {result}")
        return result
    
    @pyqtSlot(int)
    def receiveCalculationResult(self, result: int) -> None:
        """接收Web页面返回的计算结果"""
        info(f"收到Web计算结果: {result}")
    
    def send_message_to_web(self, message: str) -> None:
        """发送消息到Web页面"""
        self.messageFromQt.emit(message)
    
    def send_json_to_web(self, data: dict) -> None:
        """发送JSON数据到Web页面"""
        self.jsonFromQt.emit(data)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
