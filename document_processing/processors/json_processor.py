# processors/json_processor.py
import json
from typing import Optional, Any
import logging

class JSONProcessor:
    @staticmethod
    def _parse_json_value(value: Any) -> str:
        """递归解析JSON值"""
        if isinstance(value, dict):
            return "\n".join([f"{k}: {JSONProcessor._parse_json_value(v)}" for k, v in value.items()])
        elif isinstance(value, list):
            return "\n".join([JSONProcessor._parse_json_value(item) for item in value])
        else:
            return str(value)

    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """提取JSON内容（扁平化处理）"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return JSONProcessor._parse_json_value(data)
        except Exception as e:
            logging.error(f"JSON处理失败: {str(e)}")
            return None