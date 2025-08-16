import logging
import sys
from pathlib import Path
from typing import Optional

class Logger:
    """日志工具类，提供统一的日志配置和接口"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "PyQt6Browser", log_file: str = "app_debug.log"):
        if hasattr(self, "logger"):
            return
            
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
            
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """获取日志实例"""
        if not cls._instance:
            cls()
        return cls._instance.logger

# 便捷的日志函数
def debug(message: str, *args, **kwargs) -> None:
    Logger.get_logger().debug(message, *args, **kwargs)

def info(message: str, *args, **kwargs) -> None:
    Logger.get_logger().info(message, *args, **kwargs)

def warning(message: str, *args, **kwargs) -> None:
    Logger.get_logger().warning(message, *args, **kwargs)

def error(message: str, *args, **kwargs) -> None:
    Logger.get_logger().error(message, *args, **kwargs)

def critical(message: str, *args, **kwargs) -> None:
    Logger.get_logger().critical(message, *args, **kwargs)
