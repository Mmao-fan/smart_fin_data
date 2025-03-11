# -*- coding: utf-8 -*-
import os
import logging
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Union, Generator
import traceback
import re
import sys
import importlib
from datetime import datetime
from io import StringIO
import numpy as np
from collections import defaultdict
import subprocess

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


# 检查模块是否已安装
def is_module_installed(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


# 安装缺失的模块
def install_module(module_name):
    try:
        logging.info(f"正在安装 {module_name} 模块...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        logging.info(f"{module_name} 模块安装成功")
        return True
    except Exception as e:
        logging.error(f"{module_name} 模块安装失败: {str(e)}")
        return False


# 检查并安装 python-docx 模块
HAS_DOCX = is_module_installed('docx')
if not HAS_DOCX:
    logging.warning("python-docx 模块未安装，尝试自动安装...")
    if install_module('python-docx'):
        HAS_DOCX = True
        from docx import Document
    else:
        logging.warning("python-docx 模块安装失败，Word处理功能将受限")
else:
    logging.info("python-docx 模块已安装")
    from docx import Document

# 检查并安装 PyPDF2
HAS_PYPDF2 = is_module_installed('PyPDF2')
if not HAS_PYPDF2:
    logging.warning("PyPDF2 模块未安装，尝试自动安装...")
    if install_module('PyPDF2'):
        HAS_PYPDF2 = True
        import PyPDF2
    else:
        logging.warning("PyPDF2 模块未安装，PDF处理功能将受限")
else:
    logging.info("PyPDF2 模块已安装")
    import PyPDF2

# 不安装spacy，使用离线模式
HAS_SPACY = False
logging.info("使用离线模式进行实体识别和文本处理")

# 检查并安装必要的依赖
required_modules = {
    'pandas': 'pandas',
    'python-docx': 'docx',
    'PyPDF2': 'PyPDF2',
    'scikit-learn': 'sklearn'
}

for module_name, import_name in required_modules.items():
    if not is_module_installed(import_name):
        logging.warning(f"{module_name} 模块未安装，尝试自动安装...")
        if install_module(module_name):
            logging.info(f"{module_name} 模块安装成功")
        else:
            logging.warning(f"{module_name} 模块安装失败，部分功能可能受限")
    else:
        logging.info(f"{module_name} 模块已安装")

# 尝试导入其他模块，如果导入失败则提供替代方案
try:
    from document_processing.document_processor import DocumentProcessor

    HAS_DOCUMENT_PROCESSOR = True
except ImportError:
    HAS_DOCUMENT_PROCESSOR = False
    logging.warning("DocumentProcessor 模块导入失败，只能处理CSV文件、Word文件和PDF文件")

try:
    from text_chunking.chunk_manager import ChunkManager
    from information_extraction.anomaly_detector import AnomalyDetector
    from information_extraction.information_extractor import InformationProcessor

    HAS_TEXT_PROCESSING = True
except ImportError:
    HAS_TEXT_PROCESSING = False
    logging.warning("文本处理模块导入失败，部分功能将受限")

try:
    from scenario_adaptation.customer_service_generator import CustomerServiceGenerator
    from scenario_adaptation.fraud_encoder import FraudEncoder
    from scenario_adaptation.compliance_mapper import ComplianceMapper
    from config import CUSTOMER_SERVICE_CONFIG

    HAS_SCENARIO_ADAPTATION = True
except ImportError:
    HAS_SCENARIO_ADAPTATION = False
    logging.warning("场景适配模块导入失败，部分功能将受限")


def detect_file_encoding(file_path: str) -> str:
    """检测文件编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(100)  # 尝试读取前100个字符
                return encoding
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，默认返回utf-8
    return 'utf-8'


def chunk_large_file(file_path: str, chunk_size: int = 1024 * 1024) -> Generator[str, None, None]:
    """分块读取大文件"""
    encoding = detect_file_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk


def extract_advanced_keywords(text: str) -> Dict[str, List[str]]:
    """增强的关键词提取"""
    keywords = defaultdict(list)

    # 使用更复杂的模式匹配
    patterns = {
        'banks': [
            r"([A-Za-z\s]+(?:Bank|Financial|Credit Union))",
            r"([\u4e00-\u9fa5]+(?:银行|信用社|金融))",
        ],
        'companies': [
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:Inc|Corp|Ltd|LLC|Company|Group))",
            r"([\u4e00-\u9fa5]+(?:公司|集团|企业|有限责任|股份))",
        ],
        'dates': [
            r"(\d{4}(?:/\d{1,2}){2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日)",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
        ],
        'amounts': [
            r"(\d+(?:\.\d+)?)\s*(?:亿|万|元|美元|USD|CNY|RMB|€|₤|¥)",
            r"(?:USD|CNY|RMB|€|₤|¥)\s*(\d+(?:\.\d+)?)",
        ],
        'locations': [
            r"([\u4e00-\u9fa5]{2,}(?:省|市|区|县|镇))",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s+City)?)",
        ],
        'emails': [
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        ],
        'phones': [
            r"(\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
            r"(\d{3,4}[-\s]?\d{3,4}[-\s]?\d{4})",
        ],
    }

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, text)
            for match in matches:
                value = match.group(1).strip()
                if value and value not in keywords[category]:
                    keywords[category].append(value)

    return dict(keywords)


def extract_document_structure(content: str) -> Dict[str, Any]:
    """提取文档结构"""
    structure = {
        'paragraphs': [],
        'sections': [],
        'lists': [],
        'tables': [],
    }

    # 分析段落
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
    structure['paragraphs'] = paragraphs

    # 识别章节
    section_pattern = r'^(?:第[一二三四五六七八九十]+[章节]|[IVX]+\.|[\d]+\.)\s*(.+)$'
    for para in paragraphs:
        if re.match(section_pattern, para, re.MULTILINE):
            structure['sections'].append(para)

    # 识别列表
    list_pattern = r'(?:^[\d]+\.|^[-•*]\s+)(.+)$'
    current_list = []
    for para in paragraphs:
        if re.match(list_pattern, para, re.MULTILINE):
            current_list.append(para)
        elif current_list:
            if len(current_list) > 1:
                structure['lists'].append(current_list.copy())
            current_list = []

    # 识别表格（简单表格）
    table_pattern = r'[|｜].+[|｜]'
    current_table = []
    for para in paragraphs:
        if re.match(table_pattern, para):
            current_table.append(para)
        elif current_table:
            if len(current_table) > 1:
                structure['tables'].append(current_table.copy())
            current_table = []

    return structure


def process_csv_file(file_path: str) -> Dict[str, Any]:
    """增强的CSV文件处理"""
    try:
        logging.info(f"处理CSV文件: {file_path}")

        # 检测文件编码
        encoding = detect_file_encoding(file_path)
        logging.info(f"检测到文件编码: {encoding}")

        # 尝试不同的分隔符
        separators = [',', ';', '\t', '|']
        df = None
        used_sep = None

        for sep in separators:
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                used_sep = sep
                break
            except:
                continue

        if df is None:
            raise ValueError("无法识别CSV文件格式")

        # 数据清洗和预处理
        df = df.replace(['', 'null', 'NULL', 'NaN', 'nan'], np.nan)

        # 识别列类型
        column_types = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                # 尝试转换为日期，支持多种日期格式
                date_formats = [
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%d/%m/%Y',
                    '%m/%d/%Y',
                    '%Y%m%d',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S'
                ]
                is_date = False
                for date_format in date_formats:
                    try:
                        pd.to_datetime(df[col], format=date_format, errors='raise')
                        column_types[col] = 'date'
                        is_date = True
                        break
                    except:
                        continue

                if not is_date:
                    # 检查是否是数值（带有货币符号等）
                    try:
                        if df[col].str.contains(r'[\d]+').all():
                            column_types[col] = 'numeric_string'
                        else:
                            column_types[col] = 'text'
                    except:
                        column_types[col] = 'text'
            else:
                column_types[col] = str(df[col].dtype)

        # 构建结构化数据
        structured_data = {
            'type': 'tabular_data',
            'data': df.to_dict(orient='records'),
            'columns': df.columns.tolist(),
            'column_types': column_types,
            'row_count': len(df),
            'metadata': {
                'file_path': file_path,
                'file_type': '.csv',
                'encoding': encoding,
                'separator': used_sep,
                'file_size': os.path.getsize(file_path),
                'processed_time': pd.Timestamp.now().isoformat()
            },
            'statistics': {
                'missing_values': df.isnull().sum().to_dict(),
                'unique_values': {col: df[col].nunique() for col in df.columns},
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist()
            }
        }

        return structured_data

    except Exception as e:
        logging.error(f"处理CSV文件失败: {str(e)}", exc_info=True)
        return None


def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
    """增强的Word文档文本提取"""
    if not HAS_DOCX:
        return None

    try:
        doc = Document(file_path)
        document_data = {
            'paragraphs': [],
            'tables': [],
            'sections': [],
            'headers': [],
            'footers': [],
            'images': [],
            'styles': set()
        }

        # 提取段落
        for para in doc.paragraphs:
            if para.text.strip():
                para_data = {
                    'text': para.text.strip(),
                    'style': para.style.name,
                    'alignment': str(para.alignment) if para.alignment else 'LEFT'
                }
                # 安全地获取段落格式属性
                try:
                    if hasattr(para.paragraph_format, 'first_line_indent'):
                        para_data['first_line_indent'] = para.paragraph_format.first_line_indent
                    if hasattr(para.paragraph_format, 'left_indent'):
                        para_data['left_indent'] = para.paragraph_format.left_indent
                    if hasattr(para.paragraph_format, 'right_indent'):
                        para_data['right_indent'] = para.paragraph_format.right_indent
                except:
                    pass

                document_data['paragraphs'].append(para_data)
                document_data['styles'].add(para.style.name)

        # 提取表格
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_data = {
                        'text': cell.text.strip()
                    }
                    # 安全地获取单元格跨度
                    try:
                        if hasattr(cell._tc, 'tcPr') and cell._tc.tcPr:
                            if hasattr(cell._tc.tcPr, 'gridSpan'):
                                cell_data['spans'] = len(cell._tc.tcPr.gridSpan)
                    except:
                        cell_data['spans'] = 1
                    row_data.append(cell_data)
                table_data.append(row_data)
            document_data['tables'].append(table_data)

        # 提取节
        for section in doc.sections:
            section_data = {
                'start_type': str(section.start_type) if hasattr(section, 'start_type') else None,
                'orientation': str(section.orientation) if hasattr(section, 'orientation') else None,
                'page_height': float(section.page_height.cm) if hasattr(section, 'page_height') else None,
                'page_width': float(section.page_width.cm) if hasattr(section, 'page_width') else None
            }

            # 安全地提取页眉页脚
            try:
                if section.header and section.header.paragraphs:
                    section_data['header'] = "\n".join(
                        p.text.strip() for p in section.header.paragraphs if p.text.strip())
                else:
                    section_data['header'] = None
            except:
                section_data['header'] = None

            try:
                if section.footer and section.footer.paragraphs:
                    section_data['footer'] = "\n".join(
                        p.text.strip() for p in section.footer.paragraphs if p.text.strip())
                else:
                    section_data['footer'] = None
            except:
                section_data['footer'] = None

            document_data['sections'].append(section_data)

        document_data['styles'] = list(document_data['styles'])
        return document_data

    except Exception as e:
        logging.error(f"提取Word文档文本失败: {str(e)}")
        return None


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """增强的PDF文档文本提取"""
    if not HAS_PYPDF2:
        return None

    try:
        document_data = {
            'pages': [],
            'metadata': {},
            'images': [],
            'forms': [],
            'links': []
        }

        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # 提取元数据
            document_data['metadata'] = {
                'title': reader.metadata.get('/Title', ''),
                'author': reader.metadata.get('/Author', ''),
                'subject': reader.metadata.get('/Subject', ''),
                'creator': reader.metadata.get('/Creator', ''),
                'producer': reader.metadata.get('/Producer', ''),
                'creation_date': reader.metadata.get('/CreationDate', ''),
                'modification_date': reader.metadata.get('/ModDate', '')
            }

            # 提取页面内容
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_data = {
                    'number': page_num + 1,
                    'text': page.extract_text() or "",
                    'size': {
                        'width': float(page.mediabox.width),
                        'height': float(page.mediabox.height)
                    },
                    'rotation': page.get('/Rotate', 0)
                }

                # 提取表单字段
                if '/AcroForm' in page:
                    form_fields = []
                    try:
                        for annot in page['/Annots']:
                            if isinstance(annot, PyPDF2.generic.IndirectObject):
                                annot = annot.get_object()
                            if annot.get('/FT'):
                                field_data = {
                                    'type': str(annot['/FT']),
                                    'name': str(annot.get('/T', '')),
                                    'value': str(annot.get('/V', ''))
                                }
                                form_fields.append(field_data)
                    except:
                        pass
                    page_data['forms'] = form_fields

                # 提取链接
                if hasattr(page, 'annotations'):
                    links = []
                    try:
                        for annot in page.annotations:
                            if isinstance(annot, PyPDF2.generic.IndirectObject):
                                annot = annot.get_object()
                            if annot.get('/Subtype') == '/Link':
                                if annot.get('/A'):
                                    link_data = {
                                        'type': 'external',
                                        'url': str(annot['/A'].get('/URI', ''))
                                    }
                                    links.append(link_data)
                    except:
                        pass
                    page_data['links'] = links

                document_data['pages'].append(page_data)

        return document_data

    except Exception as e:
        logging.error(f"提取PDF文档文本失败: {str(e)}")
        return None


def process_docx_file(file_path: str) -> Dict[str, Any]:
    """增强的Word文档处理"""
    try:
        logging.info(f"处理Word文档: {file_path}")

        # 提取文档内容和结构
        doc_data = extract_text_from_docx(file_path)
        if not doc_data:
            return None

        # 构建完整文本
        full_text = "\n".join([p['text'] for p in doc_data['paragraphs']])

        # 提取关键信息
        keywords = extract_advanced_keywords(full_text)

        # 分析文档结构
        doc_structure = extract_document_structure(full_text)

        # 构建结构化数据
        structured_data = {
            'type': 'document',
            'content': full_text[:1000] + "..." if len(full_text) > 1000 else full_text,
            'metadata': {
                'file_path': file_path,
                'file_type': '.docx',
                'file_size': os.path.getsize(file_path),
                'processed_time': datetime.now().isoformat(),
                'document_properties': {
                    'sections': len(doc_data['sections']),
                    'tables': len(doc_data['tables']),
                    'styles': doc_data['styles']
                }
            },
            'structure': {
                'paragraphs': doc_structure['paragraphs'][:100],
                'sections': doc_structure['sections'],
                'lists': doc_structure['lists'],
                'tables': doc_structure['tables'],
                'document_elements': {
                    'tables': doc_data['tables'],
                    'headers': doc_data['headers'],
                    'footers': doc_data['footers']
                }
            },
            'keywords': keywords
        }

        return structured_data

    except Exception as e:
        logging.error(f"处理Word文档失败: {str(e)}", exc_info=True)
        return None


def process_pdf_file(file_path: str) -> Dict[str, Any]:
    """增强的PDF文档处理"""
    try:
        logging.info(f"处理PDF文档: {file_path}")

        # 提取PDF内容和结构
        pdf_data = extract_text_from_pdf(file_path)
        if not pdf_data:
            return None

        # 构建完整文本
        full_text = "\n".join([page['text'] for page in pdf_data['pages']])

        # 提取关键信息
        keywords = extract_advanced_keywords(full_text)

        # 分析文档结构
        doc_structure = extract_document_structure(full_text)

        # 构建结构化数据
        structured_data = {
            'type': 'document',
            'content': full_text[:1000] + "..." if len(full_text) > 1000 else full_text,
            'metadata': {
                'file_path': file_path,
                'file_type': '.pdf',
                'file_size': os.path.getsize(file_path),
                'processed_time': datetime.now().isoformat(),
                'pdf_metadata': pdf_data['metadata'],
                'document_properties': {
                    'pages': len(pdf_data['pages']),
                    'forms': any(page.get('forms') for page in pdf_data['pages']),
                    'links': any(page.get('links') for page in pdf_data['pages'])
                }
            },
            'structure': {
                'paragraphs': doc_structure['paragraphs'][:100],
                'sections': doc_structure['sections'],
                'lists': doc_structure['lists'],
                'tables': doc_structure['tables'],
                'pdf_elements': {
                    'pages': [{
                        'number': page['number'],
                        'size': page['size'],
                        'rotation': page['rotation'],
                        'forms': page.get('forms', []),
                        'links': page.get('links', [])
                    } for page in pdf_data['pages']]
                }
            },
            'keywords': keywords
        }

        return structured_data

    except Exception as e:
        logging.error(f"处理PDF文档失败: {str(e)}", exc_info=True)
        return None


def get_file_scenario(file_path: str) -> str:
    """
    根据文件类型和内容自动选择合适的场景
    """
    _, ext = os.path.splitext(file_path)

    # 根据文件扩展名选择场景
    if ext.lower() == '.csv':
        # 检查是否包含交易相关列
        try:
            df = pd.read_csv(file_path)
            columns = [col.lower() for col in df.columns]
            if any(keyword in ' '.join(columns) for keyword in ['transaction', 'account', 'amount', 'balance']):
                return "fraud_detection"
        except:
            pass

    elif ext.lower() in ['.docx', '.doc', '.pdf', '.txt']:
        # 对于文档类型，默认使用客服问答场景
        return "customer_service"

    # 默认场景
    return "customer_service"


def process_file(file_path: str, scenario: str = None) -> Dict[str, Any]:
    """
    处理单个文件
    """
    try:
        logging.info(f"开始处理文件: {file_path}")

        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)

        # 如果未指定场景，自动选择
        if scenario is None:
            scenario = get_file_scenario(file_path)
            logging.info(f"自动选择场景: {scenario}")

        # 根据文件类型选择处理方法
        if ext.lower() == '.csv':
            structured_data = process_csv_file(file_path)
            if not structured_data:
                return None
        elif ext.lower() in ['.docx', '.doc']:
            structured_data = process_docx_file(file_path)
            if not structured_data:
                return None
        elif ext.lower() == '.pdf':
            structured_data = process_pdf_file(file_path)
            if not structured_data:
                return None
        else:
            # 其他类型文件使用文档处理器
            if not HAS_DOCUMENT_PROCESSOR:
                logging.error(f"无法处理 {ext} 类型文件，DocumentProcessor 模块未加载")
                return None

            structured_data = DocumentProcessor.process_document(file_path)

        logging.info(f"文件 {file_path} 结构化处理完成")

        # 根据场景进行特定处理
        if scenario == "fraud_detection" and structured_data['type'] == 'tabular_data' and HAS_SCENARIO_ADAPTATION:
            # 处理交易数据
            encoder = FraudEncoder()
            for record in structured_data['data']:
                encoder.add_transaction_chunk(pd.Series(record))
            suspicious_patterns = encoder.detect_suspicious_patterns()

            # 添加分析结果
            structured_data['analysis'] = {
                'suspicious_patterns': suspicious_patterns,
                'transaction_graph': {
                    'nodes': list(encoder.graph.nodes(data=True)),
                    'edges': list(encoder.graph.edges(data=True))
                }
            }

            logging.info(f"发现 {len(suspicious_patterns)} 个可疑交易模式")
        elif scenario == "customer_service" and HAS_SCENARIO_ADAPTATION:
            # 处理客户服务场景
            try:
                # 创建客服生成器
                generator = CustomerServiceGenerator(CUSTOMER_SERVICE_CONFIG)

                # 提取文档内容
                if structured_data['type'] == 'document':
                    document_content = structured_data['content']

                    # 分段处理长文档
                    paragraphs = structured_data['structure']['paragraphs']
                    dialogs = []

                    # 对每个段落生成对话
                    for i, para in enumerate(paragraphs):
                        if len(para.strip()) > 10:  # 忽略太短的段落
                            dialog = generator.generate_dialog({"text": para})
                            dialogs.append(dialog)

                            # 最多处理10个段落
                            if i >= 9:
                                break
                else:
                    document_content = json.dumps(structured_data)
                    dialogs = [generator.generate_dialog({"text": document_content})]

                # 添加到结构化数据
                structured_data['customer_service'] = {
                    'dialogs': dialogs,
                    'dialog_count': len(dialogs)
                }

                logging.info(f"生成 {len(dialogs)} 个客服对话")
            except Exception as e:
                logging.error(f"客服场景处理失败: {str(e)}", exc_info=True)
                structured_data['customer_service'] = {
                    'error': str(e),
                    'dialogs': []
                }
        elif scenario == "compliance" and HAS_SCENARIO_ADAPTATION and HAS_TEXT_PROCESSING:
            # 处理合规场景
            chunks = ChunkManager(mode="structure").chunk_text(json.dumps(structured_data))
            processed_chunks = InformationProcessor().process_chunks(chunks)
            mapper = ComplianceMapper()
            structured_data['compliance'] = [mapper.map_clause(c) for c in processed_chunks]
        
        # 增强功能：生成问答对
        if HAS_TEXT_PROCESSING:
            try:
                # 提取文本内容
                text_content = ""
                if structured_data['type'] == 'document':
                    text_content = structured_data['content']
                elif structured_data['type'] == 'tabular_data':
                    # 将表格数据转换为文本
                    text_content = json.dumps(structured_data['data'][:10], ensure_ascii=False)  # 限制数量
                
                # 生成训练数据
                if text_content:
                    processor = InformationProcessor()
                    training_data = processor.extract_training_data(text_content, scenario)
                    
                    # 添加到结构化数据
                    structured_data['training_data'] = {
                        'qa_pairs': training_data['qa_pairs'],
                        'summary': training_data['summary'],
                        'metadata': training_data['metadata']
                    }
                    
                    logging.info(f"生成 {len(training_data['qa_pairs'])} 个问答对")
            except Exception as e:
                logging.error(f"生成训练数据失败: {str(e)}", exc_info=True)
                structured_data['training_data'] = {
                    'error': str(e),
                    'qa_pairs': []
                }
        
        # 增强功能：隐私保护
        try:
            from information_extraction.privacy_protector import DataAnonymizer
            
            # 对敏感字段进行脱敏处理
            anonymizer = DataAnonymizer()
            
            # 处理文本内容
            if structured_data['type'] == 'document' and 'content' in structured_data:
                structured_data['content'] = anonymizer.anonymize(structured_data['content'])
            
            # 处理表格数据
            if structured_data['type'] == 'tabular_data' and 'data' in structured_data:
                structured_data['data'] = anonymizer._anonymize_tabular_data(structured_data['data'])
            
            logging.info("完成敏感信息脱敏处理")
        except Exception as e:
            logging.warning(f"隐私保护处理失败: {str(e)}")

        return structured_data

    except Exception as e:
        logging.error(f"处理文件 {file_path} 时出现异常: {str(e)}", exc_info=True)
        return None


def process_directory(data_dir: str, output_dir: str, scenario: str = None) -> List[Dict[str, Any]]:
    """
    处理整个目录中的文件
    """
    results = []
    processed_files = []
    failed_files = []

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 遍历数据目录
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path):
            try:
                # 处理文件
                file_scenario = scenario or get_file_scenario(file_path)
                logging.info(f"处理文件 {filename}，使用场景: {file_scenario}")

                result = process_file(file_path, file_scenario)
                if result:
                    # 保存结构化数据
                    output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_structured.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    processed_files.append(filename)
                    results.append(result)
                    logging.info(f"文件 {filename} 处理完成，结果保存至 {output_file}")
                else:
                    failed_files.append(filename)
            except Exception as e:
                logging.error(f"处理文件 {filename} 失败: {str(e)}", exc_info=True)
                failed_files.append(filename)

    # 生成处理报告
    report = {
        'total_files': len(os.listdir(data_dir)),
        'processed_files': processed_files,
        'failed_files': failed_files,
        'success_rate': len(processed_files) / len(os.listdir(data_dir)) if os.listdir(data_dir) else 0
    }

    # 保存处理报告
    report_file = os.path.join(output_dir, 'processing_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    # 设置目录路径
    data_dir = "data"
    output_dir = "output"

    # 启动处理流程（不指定场景，自动选择）
    results = process_directory(data_dir, output_dir)

    # 输出处理结果摘要
    print("\n处理结果摘要:")
    print(f"成功处理文件数: {len(results)}")
    print(f"详细结果请查看 output 目录下的文件")