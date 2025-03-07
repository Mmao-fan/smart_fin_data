# processors/docx_processor.py
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError


class DocxProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """保留样式信息并转换标题"""
        try:
            doc = Document(file_path)
            content = []

            for para in doc.paragraphs:
                # 处理标题样式
                if para.style.name.startswith('Heading'):
                    level = int(para.style.name.split()[-1])
                    content.append(f"{'#' * level} {para.text}")
                elif para.text.strip():
                    content.append(para.text)

            # 处理表格（保留原实现）
            for table in doc.tables:
                content.append(f"\n[Table Start]\n{cls._parse_table(table)}\n[Table End]\n")

            return "\n".join(content)

        except Exception as e:
            cls.safe_logging(file_path, e)
            raise DocumentProcessingError(f"Word处理失败: {str(e)}")

    @classmethod
    def _parse_table(cls, table) -> str:
        """优化表格空值处理"""
        markdown = []
        for i, row in enumerate(table.rows):
            cells = [
                (cell.text.strip().replace('\n', ' ') or "[空]")  # 处理空单元格
                for cell in row.cells
            ]
            markdown.append("| " + " | ".join(cells) + " |")
            if i == 0:  # 添加分隔行
                markdown.append("| " + " | ".join(["---"] * len(row.cells)) + " |")
        return "\n".join(markdown)