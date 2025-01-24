# processors/pdf_processor.py
import PyPDF2
from typing import Optional
import logging

class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """提取PDF文本内容（保留页面结构）"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text.append(f"=== Page {page_num+1} ===")
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logging.error(f"PDF处理失败: {str(e)}")
            return None