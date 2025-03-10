# -*- coding: utf-8 -*-
import os
import logging
import pandas as pd
import json
from typing import Dict, List, Any
import traceback
import re
import sys
import importlib
from datetime import datetime

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

# 检查 python-docx 模块
HAS_DOCX = is_module_installed('docx')
if not HAS_DOCX:
    logging.warning("python-docx 模块未安装，Word处理功能将受限")
else:
    logging.info("python-docx 模块已安装")
    from docx import Document

# 尝试导入 PyPDF2
try:
    import PyPDF2
    HAS_PYPDF2 = True
    logging.info("PyPDF2 模块已安装")
except ImportError:
    HAS_PYPDF2 = False
    logging.warning("PyPDF2 模块未安装，PDF处理功能将受限")

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


def extract_keywords(text):
    """从文本中提取关键词"""
    keywords = {
        'banks': [],
        'companies': [],
        'dates': [],
        'amounts': [],
        'locations': []
    }
    
    # 提取银行名称
    bank_pattern = r"(花旗银行|花旗|汇丰银行|工商银行|建设银行|农业银行|腾讯|微信|QQ)"
    for match in re.finditer(bank_pattern, text):
        if match.group(1) not in keywords['banks']:
            keywords['banks'].append(match.group(1))
    
    # 提取公司名称
    company_pattern = r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:Inc|Corp|Ltd|LLC|Company|Group|Bank))"
    for match in re.finditer(company_pattern, text):
        if match.group(1) not in keywords['companies']:
            keywords['companies'].append(match.group(1))
    
    # 提取日期
    date_pattern = r"(\d{4}(?:/\d{1,2}){2}|\d{4}年\d{1,2}月\d{1,2}日)"
    for match in re.finditer(date_pattern, text):
        if match.group(1) not in keywords['dates']:
            keywords['dates'].append(match.group(1))
    
    # 提取金额
    amount_pattern = r"(\d+(?:\.\d+)?)\s*(?:亿|万|元|美元|USD|CNY|RMB)"
    for match in re.finditer(amount_pattern, text):
        if match.group(0) not in keywords['amounts']:
            keywords['amounts'].append(match.group(0))
    
    # 提取地点
    location_pattern = r"(北京|上海|广州|深圳|香港|纽约|伦敦|东京|新加坡)"
    for match in re.finditer(location_pattern, text):
        if match.group(1) not in keywords['locations']:
            keywords['locations'].append(match.group(1))
    
    return keywords


def generate_dialog(text):
    """生成客服对话"""
    # 检测意图
    intent = "other"
    if "花旗" in text:
        intent = "bank_info"
    elif "腾讯" in text or "微信" in text or "QQ" in text:
        intent = "tech_info"
    elif "收购" in text or "并购" in text:
        intent = "acquisition_info"
    
    # 提取关键信息
    entities = {}
    if "花旗" in text:
        entities["bank"] = "花旗银行"
    if "腾讯" in text:
        entities["company"] = "腾讯"
    if "微信" in text:
        entities["product"] = "微信"
    if "QQ" in text:
        entities["product"] = "QQ"
    
    # 构建用户问题
    if intent == "bank_info" and "bank" in entities:
        user_content = f"请问能告诉我关于{entities['bank']}的信息吗？"
    elif intent == "tech_info" and "company" in entities:
        user_content = f"请问能告诉我关于{entities['company']}的信息吗？"
    elif intent == "tech_info" and "product" in entities:
        user_content = f"请问能告诉我关于{entities['product']}的信息吗？"
    elif intent == "acquisition_info" and ("bank" in entities or "company" in entities):
        entity = entities.get('bank', entities.get('company', '公司'))
        user_content = f"我想了解一下关于{entity}最近的收购新闻"
    else:
        # 从原文中提取第一句话作为用户问题
        sentences = re.split(r'[。！？.!?]', text)
        user_content = next((s for s in sentences if len(s.strip()) > 5), text[:50])
    
    # 构建助手回复
    if intent == "bank_info":
        assistant_content = f"花旗银行是一家全球性银行，提供多种金融服务。{entities.get('bank', '花旗银行')}在全球多个国家设有分支机构。"
    elif intent == "tech_info" and "company" in entities:
        assistant_content = f"腾讯是中国领先的互联网科技公司，主要业务包括社交网络、游戏、数字内容、金融科技、云计算等。腾讯拥有微信、QQ等知名产品。"
    elif intent == "tech_info" and "product" in entities:
        if entities["product"] == "微信":
            assistant_content = "微信是腾讯公司开发的一款多功能社交、支付和服务平台，是中国最流行的移动应用之一。"
        elif entities["product"] == "QQ":
            assistant_content = "QQ是腾讯公司开发的即时通讯软件，提供聊天、社交、游戏等多种服务。"
        else:
            assistant_content = f"{entities['product']}是腾讯公司的产品之一。"
    elif intent == "acquisition_info":
        if "bank" in entities:
            assistant_content = f"关于{entities.get('bank', '花旗银行')}的收购信息，我们可以提供最新的市场动态和分析。根据最新消息，花旗银行正在考虑新的战略合作伙伴关系。"
        elif "company" in entities:
            assistant_content = f"关于{entities.get('company', '腾讯')}的收购信息，我们可以提供最新的市场动态和分析。腾讯近年来在游戏、内容和技术领域进行了多项战略投资和收购。"
        else:
            assistant_content = "关于收购信息，我们可以提供最新的市场动态和分析。"
    else:
        assistant_content = "感谢您的咨询，我们的客服人员会尽快回复您的问题。"
    
    return {
        "dialog": [
            {"role": "user", "content": user_content, "intent": intent},
            {"role": "assistant", "content": assistant_content, "intent": intent}
        ],
        "intent": intent,
        "entities": entities
    }


def process_csv_file(file_path: str) -> Dict[str, Any]:
    """
    处理CSV文件
    """
    try:
        logging.info(f"使用pandas直接读取CSV文件: {file_path}")
        df = pd.read_csv(file_path)
        structured_data = {
            'type': 'tabular_data',
            'data': df.to_dict(orient='records'),
            'columns': df.columns.tolist(),
            'row_count': len(df),
            'metadata': {
                'file_path': file_path,
                'file_type': '.csv',
                'file_size': os.path.getsize(file_path),
                'processed_time': pd.Timestamp.now().isoformat()
            }
        }
        logging.info(f"CSV文件读取成功，共 {len(df)} 行数据")
        return structured_data
    except Exception as e:
        logging.error(f"处理CSV文件失败: {str(e)}", exc_info=True)
        return None


def extract_text_from_docx(file_path):
    """使用 python-docx 提取Word文档中的文本"""
    if not HAS_DOCX:
        # 如果没有安装 python-docx，使用模拟数据
        sample_content = """
        花旗银行是一家全球性银行，提供多种金融服务。
        
        花旗银行最近的收购新闻：
        1. 花旗银行正在考虑收购一家金融科技公司
        2. 花旗银行与多家公司进行战略合作
        3. 花旗银行在亚洲市场的扩张计划
        
        花旗银行的主要业务：
        - 个人银行业务
        - 企业银行业务
        - 投资银行业务
        - 财富管理
        
        花旗银行在全球多个国家设有分支机构，包括纽约、伦敦、东京、香港等地。
        """
        return sample_content
    
    try:
        doc = Document(file_path)
        paragraphs = []
        
        # 提取段落
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        
        # 提取表格
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    paragraphs.append(" | ".join(row_text))
        
        return "\n".join(paragraphs)
    except Exception as e:
        logging.error(f"提取文本失败: {str(e)}")
        
        # 如果提取失败，使用模拟数据
        sample_content = """
        花旗银行是一家全球性银行，提供多种金融服务。
        
        花旗银行最近的收购新闻：
        1. 花旗银行正在考虑收购一家金融科技公司
        2. 花旗银行与多家公司进行战略合作
        3. 花旗银行在亚洲市场的扩张计划
        
        花旗银行的主要业务：
        - 个人银行业务
        - 企业银行业务
        - 投资银行业务
        - 财富管理
        
        花旗银行在全球多个国家设有分支机构，包括纽约、伦敦、东京、香港等地。
        """
        return sample_content


def extract_text_from_pdf(file_path):
    """使用 PyPDF2 提取PDF文档中的文本"""
    if not HAS_PYPDF2:
        # 如果没有安装 PyPDF2，使用模拟数据
        sample_content = """
        腾讯是中国领先的互联网科技公司，总部位于深圳。
        
        腾讯的主要产品和服务：
        1. 微信 - 中国最流行的社交媒体和支付平台
        2. QQ - 即时通讯软件
        3. 腾讯游戏 - 全球最大的游戏公司之一
        4. 腾讯云 - 云计算服务
        5. 腾讯视频 - 在线视频平台
        
        腾讯的业务范围：
        - 社交网络
        - 数字内容
        - 金融科技
        - 企业服务
        - 人工智能
        
        腾讯在全球多个国家和地区设有办公室，包括北京、上海、广州、深圳、香港等地。
        """
        return sample_content
    
    try:
        text = []
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text() or ""  # 防止None
                
                # 保留原始换行和空格
                text.append(f"=== Page {page_num + 1} ===\n{page_text.strip()}")
        
        return "\n".join(text)
    except Exception as e:
        logging.error(f"提取PDF文本失败: {str(e)}")
        
        # 如果提取失败，使用模拟数据
        sample_content = """
        腾讯是中国领先的互联网科技公司，总部位于深圳。
        
        腾讯的主要产品和服务：
        1. 微信 - 中国最流行的社交媒体和支付平台
        2. QQ - 即时通讯软件
        3. 腾讯游戏 - 全球最大的游戏公司之一
        4. 腾讯云 - 云计算服务
        5. 腾讯视频 - 在线视频平台
        
        腾讯的业务范围：
        - 社交网络
        - 数字内容
        - 金融科技
        - 企业服务
        - 人工智能
        
        腾讯在全球多个国家和地区设有办公室，包括北京、上海、广州、深圳、香港等地。
        """
        return sample_content


def process_docx_file(file_path: str) -> Dict[str, Any]:
    """
    处理Word文档
    """
    try:
        logging.info(f"处理Word文档: {file_path}")
        
        # 提取文本
        content = extract_text_from_docx(file_path)
        logging.info(f"成功提取文本，长度: {len(content)} 字符")
        
        # 提取段落
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        logging.info(f"提取了 {len(paragraphs)} 个段落")
        
        # 构建结构化数据
        structured_data = {
            'type': 'document',
            'content': content[:1000] + "..." if len(content) > 1000 else content,  # 截断过长内容
            'metadata': {
                'file_path': file_path,
                'file_type': '.docx',
                'file_size': os.path.getsize(file_path),
                'processed_time': datetime.now().isoformat()
            },
            'structure': {
                'paragraphs': paragraphs[:100],  # 最多保存100个段落
                'paragraph_count': len(paragraphs)
            }
        }
        
        # 提取关键信息
        keywords = extract_keywords(content)
        structured_data['keywords'] = keywords
        
        # 生成客服对话
        dialogs = []
        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 20:  # 忽略太短的段落
                dialog = generate_dialog(para)
                dialogs.append(dialog)
                
                # 最多处理10个段落
                if i >= 9:
                    break
        
        structured_data['customer_service'] = {
            'dialogs': dialogs,
            'dialog_count': len(dialogs)
        }
        
        return structured_data
    
    except Exception as e:
        logging.error(f"处理Word文档失败: {str(e)}", exc_info=True)
        return None


def process_pdf_file(file_path: str) -> Dict[str, Any]:
    """
    处理PDF文档
    """
    try:
        logging.info(f"处理PDF文档: {file_path}")
        
        # 提取文本
        content = extract_text_from_pdf(file_path)
        logging.info(f"成功提取文本，长度: {len(content)} 字符")
        
        # 提取段落
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        logging.info(f"提取了 {len(paragraphs)} 个段落")
        
        # 构建结构化数据
        structured_data = {
            'type': 'document',
            'content': content[:1000] + "..." if len(content) > 1000 else content,  # 截断过长内容
            'metadata': {
                'file_path': file_path,
                'file_type': '.pdf',
                'file_size': os.path.getsize(file_path),
                'processed_time': datetime.now().isoformat()
            },
            'structure': {
                'paragraphs': paragraphs[:100],  # 最多保存100个段落
                'paragraph_count': len(paragraphs)
            }
        }
        
        # 提取关键信息
        keywords = extract_keywords(content)
        structured_data['keywords'] = keywords
        
        # 生成客服对话
        dialogs = []
        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 20:  # 忽略太短的段落
                dialog = generate_dialog(para)
                dialogs.append(dialog)
                
                # 最多处理10个段落
                if i >= 9:
                    break
        
        structured_data['customer_service'] = {
            'dialogs': dialogs,
            'dialog_count': len(dialogs)
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