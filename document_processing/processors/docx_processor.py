# processors/docx_processor.py
from docx import Document
import logging
from .exceptions import DocumentProcessingError

class DocxProcessor:
    @staticmethod
    def _parse_table(table) -> str:
        """将Word表格转换为Markdown格式，保留表头"""
        markdown = []
        if not table.rows:
            return ""
        # 处理表头
        header_cells = table.rows[0].cells
        headers = [cell.text.strip() for cell in header_cells]
        markdown.append("| " + " | ".join(headers) + " |")
        markdown.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # 处理数据行
        for row in table.rows[1:]:
            cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            markdown.append("| " + " | ".join(cells) + " |")
        return "\n".join(markdown)

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        提取Word文档内容，包括段落和表格
        - 段落直接拼接，过滤空行
        - 表格转换为Markdown格式并用[Table]标记
        """
        try:
            doc = Document(file_path)
            content = []
            # 处理段落
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    content.append(text)
            # 处理表格
            for table in doc.tables:
                table_md = DocxProcessor._parse_table(table)
                content.append(f"\n[Table Start]\n{table_md}\n[Table End]\n")
            return "\n".join(content)
        except Exception as e:
            logging.error(f"Word处理失败: {str(e)}")
            raise DocumentProcessingError(f"Word处理失败: {str(e)}")