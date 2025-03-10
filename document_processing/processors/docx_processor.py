# -*- coding: utf-8 -*-
# processors/docx_processor.py
import logging
from pathlib import Path
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError

# 尝试导入 python-docx，如果不存在则提供一个替代方案
try:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logging.warning("python-docx 模块未安装，Word处理功能将受限")


class DocxProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """保留样式信息并转换标题"""
        try:
            if not HAS_DOCX:
                raise DocumentProcessingError("python-docx 模块未安装，无法处理Word文件。请安装 python-docx: pip install python-docx")
                
            doc = Document(file_path)
            content = []

            # 提取文档属性
            content.append("# 文档信息")
            if doc.core_properties.title:
                content.append(f"标题: {doc.core_properties.title}")
            if doc.core_properties.author:
                content.append(f"作者: {doc.core_properties.author}")
            if doc.core_properties.created:
                content.append(f"创建时间: {doc.core_properties.created}")
            if doc.core_properties.modified:
                content.append(f"修改时间: {doc.core_properties.modified}")
            content.append("")  # 空行分隔

            content.append("# 文档内容")
            for para in doc.paragraphs:
                # 处理标题样式
                if para.style.name.startswith('Heading'):
                    level = int(para.style.name.split()[-1])
                    content.append(f"{'#' * level} {para.text}")
                elif para.text.strip():
                    content.append(para.text)

            # 处理表格
            for table in doc.tables:
                content.append(f"\n[Table Start]\n{cls._parse_table(table)}\n[Table End]\n")

            return "\n".join(content)

        except Exception as e:
            cls.safe_logging(file_path, e)
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"Word处理失败: {str(e)}")

    @classmethod
    def _parse_table(cls, table) -> str:
        """优化表格空值处理"""
        if not HAS_DOCX:
            return ""
            
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