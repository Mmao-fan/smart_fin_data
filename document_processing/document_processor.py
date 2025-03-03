# document_processor.py
import os
from .processors.exceptions import DocumentProcessingError
from .processors.pdf_processor import PDFProcessor
from .processors.csv_processor import CSVProcessor
from .processors.json_processor import JSONProcessor
from .processors.excel_processor import ExcelProcessor
from .processors.docx_processor import DocxProcessor


class DocumentProcessor:
    # 文件类型与处理器映射
    PROCESSORS = {
        '.pdf': PDFProcessor,
        '.docx': DocxProcessor,
        '.xlsx': ExcelProcessor,
        '.xls': ExcelProcessor,
        '.csv': CSVProcessor,
        '.json': JSONProcessor
    }

    @classmethod
    def process_document(cls, file_path: str) -> str:
        """
        主入口：根据文件类型调用对应处理器
        - 统一抛出DocumentProcessingError
        - 文件不存在或类型不支持时直接报错
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if processor := cls.PROCESSORS.get(ext):
            return processor.extract_text(file_path)
        else:
            raise DocumentProcessingError(f"不支持的文件类型: {ext}")