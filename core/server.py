import os
import socket
import select
import threading
import time
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from utils.logger import info, error, debug
from utils.resource_manager import ResourceManager

class ServerSignals(QObject):
    """服务器信号类，用于跨线程通信"""
    started = pyqtSignal(int)  # 服务器启动成功，传递端口号
    failed = pyqtSignal(str, dict)  # 服务器启动失败，传递错误信息和详情
    stopped = pyqtSignal()  # 服务器已停止

class SilentHTTPHandler(SimpleHTTPRequestHandler):
    """静默模式的HTTP处理器，不输出访问日志"""
    def log_message(self, format, *args):
        """重写日志方法，不输出访问日志"""
        pass

class HTTPServerManager:
    """HTTP服务器管理器，负责启动、管理和停止HTTP服务器"""
    
    def __init__(self, port: int, directory: str):
        self.port = port
        self.directory = directory
        self.server: Optional[ThreadingTCPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.signals = ServerSignals()
        self.wakeup_socket = None  # 用于唤醒阻塞的服务器
    
    def start(self) -> None:
        """启动服务器线程"""
        if self.running:
            return
            
        self.running = True
        # 创建唤醒套接字对
        self.wakeup_socket = socket.socketpair()
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
    
    def _run_server(self) -> None:
        """服务器运行逻辑"""
        try:
            if not os.path.exists(self.directory):
                raise FileNotFoundError(f"服务目录不存在: {self.directory}")
            
            os.chdir(self.directory)
            # 创建服务器
            self.server = ThreadingTCPServer(
                ("", self.port), 
                SilentHTTPHandler
            )
            # 设置地址复用
            self.server.allow_reuse_address = True
            self.server.timeout = 0.1  # 缩短超时时间，加快响应停止信号
            self.signals.started.emit(self.port)
            info(f"HTTP服务器启动 | 端口: {self.port}, 目录: {self.directory}")
            
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
            error(f"服务器启动失败: {str(e)}", exc_info=True)
            self.signals.failed.emit(str(e), error_details)
        
        finally:
            self._cleanup_server()
            self.running = False
            info("HTTP服务器线程退出")
            self.signals.stopped.emit()
    
    def _cleanup_server(self) -> None:
        """清理服务器资源"""
        # 关闭唤醒套接字
        if self.wakeup_socket:
            try:
                self.wakeup_socket[0].close()
                self.wakeup_socket[1].close()
            except Exception as e:
                error(f"唤醒套接字清理失败: {str(e)}")
            self.wakeup_socket = None
        
        # 清理服务器
        if self.server:
            try:
                if hasattr(self.server, 'socket'):
                    self.server.socket.close()
                self.server.server_close()
            except Exception as e:
                error(f"服务器清理失败: {str(e)}")
            self.server = None
    
    def stop(self) -> None:
        """停止服务器"""
        if not self.running:
            return
            
        debug("开始停止HTTP服务器")
        self.running = False
        
        # 发送唤醒信号，立即中断服务器的select阻塞
        if self.wakeup_socket:
            try:
                self.wakeup_socket[1].send(b'1')  # 发送一个字节唤醒服务器
            except Exception as e:
                error(f"发送唤醒信号失败: {str(e)}")
        
        # 等待线程终止
        if self.thread and self.thread.is_alive():
            self.thread.join(0.5)  # 最多等待500ms
            if self.thread.is_alive():
                error("HTTP服务器线程未能正常终止")
