# information_extractor.py
from .entity_extractor import FinancialEntityExtractor
from .relation_extractor import FinancialRelationExtractor
from .anomaly_detector import FraudDetector
from .summarizer import ComplianceSummarizer
from .schemas import ProcessedChunk
from typing import Optional

class InformationProcessor:
    def __init__(self):
        self.entity_extractor = FinancialEntityExtractor()
        self.relation_extractor = FinancialRelationExtractor()
        self.anomaly_detector = FraudDetector()
        self.summarizer = ComplianceSummarizer()

    def process_chunk(self, chunk_id: int, text: str) -> Optional[ProcessedChunk]:
        if not text.strip():
            return None
        try:
            entities = self.entity_extractor.extract_entities(text)
            relations = self.relation_extractor.find_transfer_relations(entities, text)
            anomalies = self.anomaly_detector.detect_time_anomalies(entities, text)
            # 改进摘要触发逻辑：使用关键词+长度阈值
            summary = None
            if "条款" in text and len(text) > 200:
                summary = self.summarizer.summarize_regulation(text)
            return ProcessedChunk(
                chunk_id=chunk_id,
                original_text=text,
                entities=entities,
                relations=relations,
                summary=summary,
                anomalies=anomalies
            )
        except Exception as e:
            print(f"信息处理失败: {str(e)}")
            return None