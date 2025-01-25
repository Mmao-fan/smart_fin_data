# compliance_mapper.py
from transformers import pipeline
from typing import List, Dict, Optional
from .schemas import ComplianceClause
from information_extraction.schemas import ProcessedChunk
import re  # 将re导入移到类外部
import logging

class ComplianceMapper:
    ENTITY_MAPPING = {
        "ORG": "responsible_party",
        "LAW": "legal_basis",
        "DATE": "effective_date"
    }

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        try:
            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                min_length=30,
                max_length=150
            )
        except ImportError as e:  # 具体化异常类型
            logging.error(f"模型加载失败: {e}")
            self.summarizer = None

    def map_clause(self, chunk: ProcessedChunk) -> ComplianceClause:
        laws = self._extract_law_references(chunk.original_text)
        return ComplianceClause(
            original_text=chunk.original_text,
            summary=self._generate_summary(chunk.original_text),
            obligations=self._extract_obligations(chunk),
            law_references=laws
        )

    @staticmethod  # 声明为静态方法
    def _extract_law_references(text: str) -> List[str]:
        pattern = r"(?:依据|根据)《([^》]+)》(第[零一二三四五六七八九十百]+条)"
        matches = re.findall(pattern, text)
        return [f"《{law}》{clause}" for law, clause in matches]

    def _generate_summary(self, text: str) -> Optional[str]:
        if not self.summarizer or len(text) < 50:
            return None
        try:
            return self.summarizer(text, max_length=150)[0]['summary_text']
        except Exception as e:  # 记录异常信息
            logging.error(f"摘要生成失败: {e}")
            return None

    def _extract_obligations(self, chunk: ProcessedChunk) -> List[Dict]:
        return [
            {"type": self.ENTITY_MAPPING[ent.label], "text": ent.text}
            for ent in chunk.entities
            if ent.label in self.ENTITY_MAPPING
        ]