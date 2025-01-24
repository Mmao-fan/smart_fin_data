# information_extractor.py
from .entity_extractor import FinancialEntityExtractor
from .relation_extractor import FinancialRelationExtractor
from .anomaly_detector import FraudDetector
from .summarizer import ComplianceSummarizer
from .schemas import ProcessedChunk


class InformationProcessor:
    def __init__(self):
        self.entity_extractor = FinancialEntityExtractor()
        self.relation_extractor = FinancialRelationExtractor()
        self.anomaly_detector = FraudDetector()
        self.summarizer = ComplianceSummarizer()

    def process_chunk(self, chunk_id: int, text: str) -> ProcessedChunk:
        # 实体提取
        entities = self.entity_extractor.extract_entities(text)

        # 关系提取
        relations = self.relation_extractor.find_transfer_relations(entities, text)

        # 异常检测
        anomalies = self.anomaly_detector.detect_time_anomalies(entities, text)

        # 摘要生成
        summary = self.summarizer.summarize_regulation(text) if "条款" in text else None

        return ProcessedChunk(
            chunk_id=chunk_id,
            original_text=text,
            entities=entities,
            relations=relations,
            summary=summary,
            anomalies=anomalies
        )