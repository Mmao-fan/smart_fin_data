# processors/base_processor.py
from abc import ABC, abstractmethod
from pathlib import Path
import logging

class BaseProcessor(ABC):
    @classmethod
    @abstractmethod
    def extract_text(cls, file_path: str) -> str:
        pass

    @classmethod
    def safe_logging(cls, file_path: str, error: Exception) -> None:
        """安全的日志记录（自动脱敏路径）"""
        filename = Path(file_path).name
        logging.error(f"[{cls.__name__}] 处理失败 [文件: {filename}]: {str(error)}")