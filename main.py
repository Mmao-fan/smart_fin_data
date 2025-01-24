# main.py
from document_processing.document_processor import DocumentProcessor
from text_chunking.chunk_manager import ChunkManager
from information_extraction.information_extractor import InformationProcessor
from scenario_adaptation.customer_service_generator import CustomerServiceGenerator
from scenario_adaptation.fraud_encoder import FraudEncoder
from scenario_adaptation.compliance_mapper import ComplianceMapper
from config import CUSTOMER_SERVICE_CONFIG


def process_pipeline(input_file: str, scenario: str):
    # 通用处理
    raw_text = DocumentProcessor.process_document(input_file)
    chunks = ChunkManager(mode="structure").chunk_text(raw_text)
    processed_chunks = InformationProcessor().process_chunks(chunks)

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