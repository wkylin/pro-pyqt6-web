import socket
from typing import Optional
from config.settings import AppConfig
from .logger import info, error

class PortManager:
    """端口管理工具类，负责端口可用性检查和分配"""
    
    @staticmethod
    def is_port_available(port: int) -> bool:
        """
        检查端口是否可用
        
        Args:
            port: 要检查的端口号
            
        Returns:
            如果端口可用则返回True，否则返回False
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) != 0
        except Exception as e:
            error(f"端口检查失败 | 端口: {port}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def find_available_port(
        start_port: int = AppConfig.DEFAULT_PORT, 
        max_attempts: int = AppConfig.MAX_PORT_ATTEMPTS
    ) -> Optional[int]:
        """
        查找可用端口
        
        Args:
            start_port: 起始端口号
            max_attempts: 最大尝试次数
            
        Returns:
            找到的可用端口号，如果未找到则返回None
        """
        for port in range(start_port, start_port + max_attempts):
            if PortManager.is_port_available(port):
                info(f"找到可用端口 | 端口: {port}")
                return port
                
        error(f"端口查找失败 | 尝试范围: {start_port}-{start_port + max_attempts - 1}")
        return None
