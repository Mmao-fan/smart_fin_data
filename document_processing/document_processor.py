# document_processor.py
import os
import pandas as pd
import json
from typing import Dict, Any, Union, Optional
from .processors.exceptions import DocumentProcessingError
from .processors.pdf_processor import PDFProcessor
from .processors.csv_processor import CSVProcessor
from .processors.json_processor import JSONProcessor
from .processors.excel_processor import ExcelProcessor
from .processors.docx_processor import DocxProcessor
import logging
from docx import Document
import PyPDF2


class DocumentProcessor:
    """文档处理器，用于处理不同类型的文档"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # 文件类型与处理器映射
    PROCESSORS = {
        '.pdf': PDFProcessor,
        '.docx': DocxProcessor,
        '.xlsx': ExcelProcessor,
        '.xls': ExcelProcessor,
        '.csv': CSVProcessor,
        '.json': JSONProcessor,
        '.txt': None  # 文本文件直接读取
    }

    @classmethod
    def process_document(cls, file_path: str) -> Union[str, Dict[str, Any]]:
        """
        主入口：根据文件类型调用对应处理器，返回结构化数据或文本内容
        Args:
            file_path: 文件路径
        Returns:
            Union[str, Dict[str, Any]]: 文本内容或结构化数据
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        
        # 处理文本文件
        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        return f.read()
                except Exception as e:
                    raise DocumentProcessingError(f"读取文本文件失败: {str(e)}")
        
        # 处理其他类型文件
        if processor := cls.PROCESSORS.get(ext):
            try:
                return processor.extract_text(file_path)
            except Exception as e:
                raise DocumentProcessingError(f"处理文件失败: {str(e)}")
        else:
            raise DocumentProcessingError(f"不支持的文件类型: {ext}")

    @classmethod
    def _process_by_type(cls, file_path: str, raw_text: str, file_type: str) -> Dict[str, Any]:
        """
        根据文件类型进行结构化处理
        """
        try:
            if file_type == '.csv':
                # 处理CSV文件
                df = pd.read_csv(file_path)
                return {
                    'type': 'tabular_data',
                    'data': df.to_dict(orient='records'),
                    'columns': df.columns.tolist(),
                    'row_count': len(df)
                }
            elif file_type == '.json':
                # 处理JSON文件
                data = json.loads(raw_text)
                return {
                    'type': 'json_data',
                    'data': data
                }
            elif file_type in ['.xlsx', '.xls']:
                # 处理Excel文件
                df = pd.read_excel(file_path)
                return {
                    'type': 'tabular_data',
                    'data': df.to_dict(orient='records'),
                    'columns': df.columns.tolist(),
                    'row_count': len(df)
                }
            elif file_type == '.pdf':
                # 处理PDF文件
                return {
                    'type': 'document',
                    'content': raw_text,
                    'sections': cls._split_into_sections(raw_text)
                }
            elif file_type == '.docx':
                # 处理Word文件
                return {
                    'type': 'document',
                    'content': raw_text,
                    'sections': cls._split_into_sections(raw_text)
                }
            else:
                # 默认处理方式
                return {
                    'type': 'text',
                    'content': raw_text
                }
        except Exception as e:
            raise DocumentProcessingError(f"文件处理失败: {str(e)}")

    @staticmethod
    def _split_into_sections(text: str) -> list:
        """
        将文本分割成段落
        """
        # 使用空行分割段落
        sections = [section.strip() for section in text.split('\n\n') if section.strip()]
        return sections

    @classmethod
    def save_structured_data(cls, data: Dict[str, Any], output_dir: str) -> str:
        """
        保存结构化数据到文件
        Args:
            data: 结构化数据
            output_dir: 输出目录
        Returns:
            str: 输出文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'structured_data_{timestamp}.json')
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_file

    def process_word(self, file_path: str) -> str:
        """处理Word文档并返回文本内容"""
        try:
            self.logger.info(f"开始处理Word文件: {file_path}")
            
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            if not text.strip():
                self.logger.warning(f"Word文件 {file_path} 提取的文本为空")
                return ""
                
            self.logger.info(f"成功从Word提取文本，长度: {len(text)}")
            return text
            
        except ImportError:
            self.logger.error("python-docx模块未安装")
            return ""
        except Exception as e:
            self.logger.error(f"处理Word文件失败: {str(e)}")
            return ""
    
    def process_pdf(self, file_path: str) -> str:
        """处理PDF文档并返回文本内容"""
        try:
            self.logger.info(f"开始处理PDF文件: {file_path}")
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                    
            if not text.strip():
                self.logger.warning(f"PDF文件 {file_path} 提取的文本为空")
                return ""
                
            self.logger.info(f"成功从PDF提取文本，长度: {len(text)}")
            return text
            
        except ImportError:
            self.logger.error("PyPDF2模块未安装")
            return ""
        except Exception as e:
            self.logger.error(f"处理PDF文件失败: {str(e)}")
            return ""
    
    def process_csv(self, file_path: str) -> str:
        """处理CSV文件并返回文本内容"""
        try:
            self.logger.info(f"开始处理CSV文件: {file_path}")
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 将DataFrame转换为字符串
            text = df.to_string()
            
            if not text.strip():
                self.logger.warning(f"CSV文件 {file_path} 提取的文本为空")
                return ""
                
            self.logger.info(f"成功从CSV提取文本，长度: {len(text)}")
            return text
            
        except Exception as e:
            self.logger.error(f"处理CSV文件失败: {str(e)}")
            return ""

    def process_text(self, file_path: str) -> str:
        """处理文本文件"""
        try:
            self.logger.info(f"开始处理文本文件: {file_path}")
            
            # 读取文本文件
            with open(file_path, 'r') as file:
                text = file.read()
            
            if not text.strip():
                self.logger.warning(f"文本文件 {file_path} 为空")
                return ""
                
            self.logger.info(f"成功读取文本文件，长度: {len(text)}")
            return text
            
        except Exception as e:
            self.logger.error(f"处理文本文件失败: {str(e)}")
            return ""