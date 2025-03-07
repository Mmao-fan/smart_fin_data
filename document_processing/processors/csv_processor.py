# processors/csv_processor.py
import csv
import chardet
import logging
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError


class CSVProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """自动检测编码，处理各种分隔符"""
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                rawdata = f.read(10000)
                encoding = chardet.detect(rawdata)['encoding'] or 'utf-8'

            # 自动检测分隔符
            with open(file_path, 'r', encoding=encoding) as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.reader(f, dialect)
                data = [row for row in reader]

            if not data:
                raise DocumentProcessingError("CSV文件内容为空")

            return cls._convert_to_markdown(data)

        except Exception as e:
            cls.safe_logging(file_path, e)
            raise DocumentProcessingError(f"CSV处理失败: {str(e)}")

    @staticmethod
    def _convert_to_markdown(data: list) -> str:
        header = data[0]
        sep = ["---"] * len(header)
        rows = [header, sep] + data[1:]
        return "\n".join("| " + " | ".join(row) + " |" for row in rows)