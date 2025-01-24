# processors/csv_processor.py
import pandas as pd
import logging
from .exceptions import DocumentProcessingError

class CSVProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """将CSV转换为Markdown表格，自动识别表头"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                raise DocumentProcessingError("CSV文件为空")
            return df.to_markdown(index=False)
        except pd.errors.EmptyDataError:
            logging.error("CSV文件为空")
            raise DocumentProcessingError("CSV文件为空")
        except Exception as e:
            logging.error(f"CSV处理失败: {str(e)}")
            raise DocumentProcessingError(f"CSV处理失败: {str(e)}")