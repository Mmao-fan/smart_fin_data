# document_processor.py
import os
from typing import Optional
from .processors.pdf_processor import PDFProcessor
from .processors.docx_processor import DocxProcessor
from .processors.excel_processor import ExcelProcessor
from .processors.csv_processor import CSVProcessor
from .processors.json_processor import JSONProcessor

class DocumentProcessor:
    # 文件类型与处理器映射表
    PROCESSORS = {
        '.pdf': PDFProcessor,
        '.docx': DocxProcessor,
        '.xlsx': ExcelProcessor,
        '.xls': ExcelProcessor,
        '.csv': CSVProcessor,
        '.json': JSONProcessor
    }

    @classmethod
    def process_document(cls, file_path: str) -> Optional[str]:
        """主处理入口"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if processor := cls.PROCESSORS.get(ext):
            return processor.extract_text(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")