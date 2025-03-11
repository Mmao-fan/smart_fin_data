# -*- coding: utf-8 -*-
# processors/csv_processor.py
import csv
import chardet
import logging
import pandas as pd
from .base_processor import BaseProcessor
from .exceptions import DocumentProcessingError
from typing import Dict, Any


class CSVProcessor(BaseProcessor):
    @classmethod
    def extract_text(cls, file_path: str) -> Dict[str, Any]:
        """自动检测编码，处理各种分隔符"""
        try:
            # 使用pandas读取CSV文件，更加健壮
            try:
                # 首先尝试使用pandas直接读取
                df = pd.read_csv(file_path)
                data = [df.columns.tolist()] + df.values.tolist()
                encoding = 'utf-8'
                delimiter = ','
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
                    raise DocumentProcessingError("无法识别CSV文件格式")

            # 将数据转换为文本
            text_content = '\n'.join([delimiter.join(map(str, row)) for row in data])
            
            return {
                'text': text_content,
                'text_chunks': [text_content],  # 作为单个块
                'total_pages': 1,  # CSV文件视为单页
                'metadata': {
                    'encoding': encoding,
                    'delimiter': delimiter,
                    'rows': len(data),
                    'columns': len(data[0]) if data else 0
                }
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"处理CSV文件失败: {str(e)}")

    @staticmethod
    def _convert_to_markdown(data: list) -> str:
        """将数据转换为Markdown表格格式"""
        if not data:
            return ""
            
        header = data[0]
        sep = ["---"] * len(header)
        rows = [header, sep] + data[1:]
        return "\n".join("| " + " | ".join(row) + " |" for row in rows)