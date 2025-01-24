# processors/excel_processor.py
import pandas as pd
from typing import Optional
import logging

class ExcelProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """提取Excel内容（所有Sheet转换为Markdown表格）"""
        try:
            xls = pd.ExcelFile(file_path)
            output = []
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                output.append(f"=== Sheet '{sheet_name}' ===")
                output.append(df.to_markdown(index=False))
            return "\n\n".join(output)
        except Exception as e:
            logging.error(f"Excel处理失败: {str(e)}")
            return None