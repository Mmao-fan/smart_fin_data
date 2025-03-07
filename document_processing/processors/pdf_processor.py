# processors/pdf_processor.py
import PyPDF2
import logging
from pathlib import Path
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError


class PDFProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """支持混合型PDF（文本+图像），智能检测扫描件"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""  # 防止None

                    # 增强扫描件检测逻辑
                    if cls._is_scanned_page(page):
                        raise DocumentProcessingError(
                            f"检测到扫描件/图像内容（第{page_num + 1}页）"
                        )

                    # 保留原始换行和空格
                    text.append(f"=== Page {page_num + 1} ===\n{page_text.strip()}")
            return "\n".join(text)

        except Exception as e:
            cls.safe_logging(file_path, e)
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"PDF处理失败: {str(e)}")

    @staticmethod
    def _is_scanned_page(page) -> bool:
        """综合判断是否为扫描页：文本量+图像存在"""
        text = page.extract_text() or ""
        if len(text) < 50 and '/XObject' in page['/Resources']:
            return True
        return False