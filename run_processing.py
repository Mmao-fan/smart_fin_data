# run_processing.py
import os
import logging
from document_processing.document_processor import DocumentProcessor
from text_chunking.chunk_manager import ChunkManager
from information_extraction.anomaly_detector import AnomalyDetector
from information_extraction.information_extractor import InformationProcessor
from scenario_adaptation.customer_service_generator import CustomerServiceGenerator
from scenario_adaptation.fraud_encoder import FraudEncoder
from scenario_adaptation.compliance_mapper import ComplianceMapper
from config import CUSTOMER_SERVICE_CONFIG

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_pipeline(input_file: str, scenario: str):
    try:
        # 通用处理
        raw_text = DocumentProcessor.process_document(input_file)
        chunks = ChunkManager(mode="structure").chunk_text(raw_text)
        processed_chunks = InformationProcessor().process_chunks(chunks)

        # 异常检测
        anomaly_detector = AnomalyDetector()
        anomalies = []
        for chunk in chunks:
            chunk_anomalies = anomaly_detector.process_chunk(chunk)
            anomalies.extend(chunk_anomalies)

        # 场景适配
        if scenario == "customer_service":
            generator = CustomerServiceGenerator(CUSTOMER_SERVICE_CONFIG)
            return [generator.generate_dialog(c) for c in processed_chunks]
        elif scenario == "fraud_detection":
            encoder = FraudEncoder()
            for c in processed_chunks:
                encoder.add_transaction_chunk(c)
            return encoder.detect_suspicious_patterns()
        elif scenario == "compliance":
            mapper = ComplianceMapper()
            return [mapper.map_clause(c) for c in processed_chunks]
        else:
            raise ValueError(f"不支持的场景: {scenario}")
    except Exception as e:
        logging.error(f"数据处理过程中出现异常: {str(e)}")
        return None

if __name__ == "__main__":
    # 假设 Excel 文件放在 data 目录下，文件名是 bank_transactions.csv
    data_dir = "data"
    csv_file = "bank_transactions.csv"
    input_file = os.path.join(data_dir, csv_file)

    # 选择一个场景，例如 "fraud_detection"
    scenario = "fraud_detection"

    # 启动处理流程
    result = process_pipeline(input_file, scenario)
    if result:
        print("结构化数据:")
        print(result)
    else:
        print("没有生成有效的结构化数据，文件未保存。")