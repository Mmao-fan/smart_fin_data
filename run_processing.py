# -*- coding: utf-8 -*-
import os
import logging
import pandas as pd
import json
from typing import Dict, List, Any
import traceback

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 尝试导入其他模块，如果导入失败则提供替代方案
try:
    from document_processing.document_processor import DocumentProcessor
    HAS_DOCUMENT_PROCESSOR = True
except ImportError:
    HAS_DOCUMENT_PROCESSOR = False
    logging.warning("DocumentProcessor 模块导入失败，只能处理CSV文件")

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


def process_file(file_path: str, scenario: str) -> Dict[str, Any]:
    """
    处理单个文件
    """
    try:
        logging.info(f"开始处理文件: {file_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        
        # 对于CSV文件，直接使用pandas读取
        if ext.lower() == '.csv':
            structured_data = process_csv_file(file_path)
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
        elif scenario == "customer_service" and HAS_SCENARIO_ADAPTATION and HAS_TEXT_PROCESSING:
            # 处理客户服务场景
            chunks = ChunkManager(mode="structure").chunk_text(json.dumps(structured_data))
            processed_chunks = InformationProcessor().process_chunks(chunks)
            generator = CustomerServiceGenerator(CUSTOMER_SERVICE_CONFIG)
            structured_data['dialog'] = [generator.generate_dialog(c) for c in processed_chunks]
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


def process_directory(data_dir: str, output_dir: str, scenario: str) -> List[Dict[str, Any]]:
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
                result = process_file(file_path, scenario)
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
    scenario = "fraud_detection"  # 可以根据需要选择不同的场景

    # 启动处理流程
    results = process_directory(data_dir, output_dir, scenario)
    
    # 输出处理结果摘要
    print("\n处理结果摘要:")
    print(f"成功处理文件数: {len(results)}")
    print(f"详细结果请查看 output 目录下的文件")