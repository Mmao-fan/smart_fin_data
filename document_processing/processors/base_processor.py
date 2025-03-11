# processors/base_processor.py
from abc import ABC, abstractmethod
from pathlib import Path
import logging
from typing import Dict, Any, Union

class BaseProcessor(ABC):
    @classmethod
    @abstractmethod
    def extract_text(cls, file_path: str) -> Dict[str, Any]:
        """
        从文件中提取文本和相关信息
        Args:
            file_path: 文件路径
        Returns:
            Dict[str, Any]: 包含文本内容和元数据的字典
        """
        pass

    @classmethod
    def safe_logging(cls, file_path: str, error: Exception) -> None:
        """安全的日志记录（自动脱敏路径）"""
        filename = Path(file_path).name
        logging.error(f"[{cls.__name__}] 处理失败 [文件: {filename}]: {str(error)}")