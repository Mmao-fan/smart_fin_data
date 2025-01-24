# processors/docx_processor.py
from docx import Document
from typing import Optional
import logging

class DocxProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """提取Word文档内容（保留段落结构）"""
        try:
            doc = Document(file_path)
            return "\n".join(
                [para.text for para in doc.paragraphs if para.text.strip()]
            )
        except Exception as e:
            logging.error(f"Word处理失败: {str(e)}")
            return None