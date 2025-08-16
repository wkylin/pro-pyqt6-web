import os
from pathlib import Path
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from config.settings import AppConfig
from .logger import info, warning, error

class ResourceManager:
    """资源管理工具类，负责资源路径解析和资源加载"""
    
    @staticmethod
    def get_base_path() -> str:
        """获取应用程序根目录"""
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    @staticmethod
    def get_path(relative_path: str) -> str:
        """
        获取资源的绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            资源的绝对路径
        """
        base_path = ResourceManager.get_base_path()
        return os.path.join(base_path, relative_path)
    
    @staticmethod
    def exists(relative_path: str) -> bool:
        """检查资源是否存在"""
        path = ResourceManager.get_path(relative_path)
        return os.path.exists(path)
    
    @staticmethod
    def load_pixmap(
        relative_path: str, 
        width: int = 600, 
        height: int = 400
    ) -> QPixmap:
        """加载PNG图片为QPixmap"""
        pixmap_path = ResourceManager.get_path(relative_path)
        
        if not os.path.exists(pixmap_path):
            warning(f"图片文件不存在 | 路径: {pixmap_path}")
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.gray)
            return pixmap
            
        try:
            pixmap = QPixmap(pixmap_path)
            return pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        except Exception as e:
            error(f"加载图片失败 | 路径: {pixmap_path}, 错误: {str(e)}")
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.gray)
            return pixmap
    
    @staticmethod
    def load_icon(relative_path: str) -> QIcon:
        """加载图标"""
        icon_path = ResourceManager.get_path(relative_path)
        
        if not os.path.exists(icon_path):
            warning(f"图标文件不存在 | 路径: {icon_path}")
            return QIcon()
            
        try:
            return QIcon(icon_path)
        except Exception as e:
            error(f"加载图标失败 | 路径: {icon_path}, 错误: {str(e)}")
            return QIcon()
    
    @staticmethod
    def load_text(relative_path: str, encoding: str = "utf-8") -> str:
        """加载文本文件内容"""
        file_path = ResourceManager.get_path(relative_path)
        
        if not os.path.exists(file_path):
            warning(f"文本文件不存在 | 路径: {file_path}")
            return ""
            
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            error(f"加载文本文件失败 | 路径: {file_path}, 错误: {str(e)}")
            return ""
