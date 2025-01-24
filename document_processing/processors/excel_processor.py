# processors/excel_processor.py
import pandas as pd
import logging
from .exceptions import DocumentProcessingError

class ExcelProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """提取Excel所有Sheet为Markdown表格"""
        try:
            xls = pd.ExcelFile(file_path)
            output = []
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if df.empty:
                    output.append(f"=== Sheet '{sheet_name}' (空) ===")
                else:
                    output.append(f"=== Sheet '{sheet_name}' ===")
                    output.append(df.to_markdown(index=False))
            return "\n\n".join(output)
        except Exception as e:
            logging.error(f"Excel处理失败: {str(e)}")
            raise DocumentProcessingError(f"Excel处理失败: {str(e)}")