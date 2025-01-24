# processors/csv_processor.py
import pandas as pd
from typing import Optional
import logging

class CSVProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """提取CSV内容（转换为Markdown表格）"""
        try:
            df = pd.read_csv(file_path)
            return df.to_markdown(index=False)
        except Exception as e:
            logging.error(f"CSV处理失败: {str(e)}")
            return None