# processors/csv_processor.py
import pandas as pd
import logging
from .exceptions import DocumentProcessingError

class CSVProcessor:
    @staticmethod
    def extract_text(file_path: str, encoding: str = 'utf-8', date_columns: list = None) -> str:
        """
        将 CSV 转换为 Markdown 表格，自动识别表头。

        参数:
        file_path (str): CSV 文件的路径。
        encoding (str, 可选): CSV 文件的编码，默认为 'utf-8'。
        date_columns (list, 可选): 包含日期列的列名列表，默认为 None。

        返回:
        str: Markdown 表格格式的字符串。
        """
        try:
            # 读取 CSV 文件，指定日期列的格式
            df = pd.read_csv(file_path, encoding=encoding, parse_dates=date_columns)

            if df.empty:
                raise DocumentProcessingError("CSV 文件为空")

            return df.to_markdown(index=False)

        except pd.errors.EmptyDataError:
            logging.error("CSV 文件为空")
            raise DocumentProcessingError("CSV 文件为空")
        except pd.errors.ParserError as e:
            # 处理解析错误
            logging.error(f"CSV 解析错误: {str(e)}")
            raise DocumentProcessingError(f"CSV 解析错误: {str(e)}")
        except UnicodeDecodeError as e:
            # 处理编码错误
            logging.error(f"CSV 编码错误: {str(e)}")
            raise DocumentProcessingError(f"CSV 编码错误: {str(e)}")
        except Exception as e:
            # 处理其他未知错误
            logging.error(f"CSV 处理失败: {str(e)}")
            raise DocumentProcessingError(f"CSV 处理失败: {str(e)}")