# compliance_mapper.py
from transformers import pipeline
from typing import List, Dict
from .schemas import ComplianceClause
from information_extraction.schemas import ProcessedChunk


def _extract_law_references(text: str) -> List[str]:
    """提取法律条文引用"""
    import re
    pattern = r"(?:依据|根据)《([^》]+)》(第[零一二三四五六七八九十百]+条)"
    matches = re.findall(pattern, text)
    return [f"《{law}》{clause}" for law, clause in matches]


class ComplianceMapper:
    ENTITY_MAPPING = {
        "ORG": "responsible_party",
        "LAW": "legal_basis",
        "DATE": "effective_date"
    }

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            min_length=30,
            max_length=150
        )

    def map_clause(self, chunk: ProcessedChunk) -> ComplianceClause:
        """将原始条款映射为结构化知识"""
        summary = self._generate_summary(chunk.original_text)
        obligations = self._extract_obligations(chunk)
        laws = _extract_law_references(chunk.original_text)

        return ComplianceClause(
            original_text=chunk.original_text,
            summary=summary,
            obligations=obligations,
            law_references=laws
        )

    def _generate_summary(self, text: str) -> str:
        """生成合规摘要"""
        return self.summarizer(
            text,
            max_length=150,
            do_sample=False
        )[0]['summary_text']

    def _extract_obligations(self, chunk: ProcessedChunk) -> List[Dict]:
        """提取义务实体"""
        obligations = []
        for ent in chunk.entities:
            if ent.label in self.ENTITY_MAPPING:
                obligations.append({
                    "type": self.ENTITY_MAPPING[ent.label],
                    "text": ent.text,
                    "position": f"{ent.start_pos}-{ent.end_pos}"
                })
        return obligations