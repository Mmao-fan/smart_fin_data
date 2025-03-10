# -*- coding: utf-8 -*-
# processors/csv_processor.py
import csv
import chardet
import logging
import pandas as pd
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError


class CSVProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """自动检测编码，处理各种分隔符"""
        try:
            # 使用pandas读取CSV文件，更加健壮
            try:
                # 首先尝试使用pandas直接读取
                df = pd.read_csv(file_path)
                data = [df.columns.tolist()] + df.values.tolist()
            except Exception as e:
                logging.warning(f"使用pandas直接读取失败: {str(e)}，尝试检测编码和分隔符")
                
                # 检测文件编码
                with open(file_path, 'rb') as f:
                    rawdata = f.read(10000)
                    encoding = chardet.detect(rawdata)['encoding'] or 'utf-8'
                
                # 尝试常见的分隔符
                delimiters = [',', ';', '\t', '|']
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=delimiter)
                        if len(df.columns) > 1:  # 确保至少有两列，说明分隔符可能是正确的
                            data = [df.columns.tolist()] + df.values.tolist()
                            logging.info(f"成功使用分隔符 '{delimiter}' 读取CSV文件")
                            break
                    except Exception:
                        continue
                else:
                    # 如果所有分隔符都失败，尝试使用csv模块的Sniffer
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            sample = f.read(4096)
                            f.seek(0)
                            dialect = csv.Sniffer().sniff(sample)
                            reader = csv.reader(f, dialect)
                            data = [row for row in reader]
                    except Exception as e:
                        # 最后的尝试：假设是逗号分隔
                        logging.warning(f"无法自动检测分隔符: {str(e)}，尝试使用逗号作为默认分隔符")
                        df = pd.read_csv(file_path, encoding=encoding, sep=',', error_bad_lines=False)
                        data = [df.columns.tolist()] + df.values.tolist()

            if not data:
                raise DocumentProcessingError("CSV文件内容为空")

            # 将数据转换为字符串
            string_data = []
            for row in data:
                string_row = []
                for item in row:
                    if pd.isna(item):
                        string_row.append("")
                    else:
                        string_row.append(str(item))
                string_data.append(string_row)

            return cls._convert_to_markdown(string_data)

        except Exception as e:
            cls.safe_logging(file_path, e)
            raise DocumentProcessingError(f"CSV处理失败: {str(e)}")

    @staticmethod
    def _convert_to_markdown(data: list) -> str:
        """将数据转换为Markdown表格格式"""
        if not data:
            return ""
            
        header = data[0]
        sep = ["---"] * len(header)
        rows = [header, sep] + data[1:]
        return "\n".join("| " + " | ".join(row) + " |" for row in rows)