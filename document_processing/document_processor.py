# document_processor.py
import os
import pandas as pd
import json
from typing import Dict, Any, Union
from .processors.exceptions import DocumentProcessingError
from .processors.pdf_processor import PDFProcessor
from .processors.csv_processor import CSVProcessor
from .processors.json_processor import JSONProcessor
from .processors.excel_processor import ExcelProcessor
from .processors.docx_processor import DocxProcessor


class DocumentProcessor:
    # 文件类型与处理器映射
    PROCESSORS = {
        '.pdf': PDFProcessor,
        '.docx': DocxProcessor,
        '.xlsx': ExcelProcessor,
        '.xls': ExcelProcessor,
        '.csv': CSVProcessor,
        '.json': JSONProcessor
    }

    @classmethod
    def process_document(cls, file_path: str) -> Dict[str, Any]:
        """
        主入口：根据文件类型调用对应处理器，返回结构化数据
        Args:
            file_path: 文件路径
        Returns:
            Dict[str, Any]: 包含结构化数据的字典
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if processor := cls.PROCESSORS.get(ext):
            # 获取原始文本
            raw_text = processor.extract_text(file_path)
            
            # 根据文件类型进行结构化处理
            structured_data = cls._process_by_type(file_path, raw_text, ext)
            
            # 添加元数据
            structured_data['metadata'] = {
                'file_path': file_path,
                'file_type': ext,
                'file_size': os.path.getsize(file_path),
                'processed_time': pd.Timestamp.now().isoformat()
            }
            
            return structured_data
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