# processors/pdf_processor.py
import PyPDF2
import logging
from .exceptions import DocumentProcessingError


class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        提取文本型PDF内容，不支持扫描件或图像型PDF
        - 每页内容标注页码（如 === Page 1 ===）
        - 若检测到扫描件，抛出异常提示需OCR处理
        """
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()

                    # 检测扫描件：若页面无文本内容，判定为扫描件
                    if not page_text.strip():
                        raise DocumentProcessingError(
                            f"检测到扫描件或图像型PDF（第{page_num + 1}页），请使用OCR模块处理"
                        )

                    # 标注页码并保存文本
                    text.append(f"=== Page {page_num + 1} ===\n{page_text}")
            return "\n".join(text)

        except DocumentProcessingError as e:
            logging.error(str(e))
            raise
        except Exception as e:
            logging.error(f"PDF解析失败: {str(e)}")
            raise DocumentProcessingError(f"PDF处理失败: {str(e)}")