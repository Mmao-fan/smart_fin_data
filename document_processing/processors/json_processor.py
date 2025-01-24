# processors/json_processor.py
import json
import logging
from typing import Any
from .exceptions import DocumentProcessingError

class JSONProcessor:
    @staticmethod
    def _parse_value(value: Any, indent: int = 0) -> str:
        """递归解析JSON值，保留缩进层级"""
        space = "  " * indent
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                lines.append(f"{space}{k}: {JSONProcessor._parse_value(v, indent + 1)}")
            return "\n".join(lines)
        elif isinstance(value, list):
            lines = []
            for item in value:
                lines.append(f"{space}- {JSONProcessor._parse_value(item, indent + 1)}")
            return "\n".join(lines)
        else:
            return str(value)

    @staticmethod
    def extract_text(file_path: str) -> str:
        """提取JSON内容，输出为层级化文本"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return JSONProcessor._parse_value(data)
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {str(e)}")
            raise DocumentProcessingError(f"无效的JSON格式: {str(e)}")
        except Exception as e:
            logging.error(f"JSON处理失败: {str(e)}")
            raise DocumentProcessingError(f"JSON处理失败: {str(e)}")