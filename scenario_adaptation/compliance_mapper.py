# compliance_mapper.py
from transformers import pipeline
from typing import List, Dict, Optional
import re
import logging

class ComplianceMapper:
    ENTITY_MAPPING = {
        "ORG": "responsible_party",
        "LAW": "legal_basis",
        "DATE": "effective_date"
    }

    def __init__(self, model_path: str = None):
        self.summarizer = None
        try:
            self.summarizer = pipeline(
                "summarization",
                model=model_path or "facebook/bart-large-cnn",
                min_length=30,
                max_length=150
            )
        except Exception as e:
            logging.error(f"模型加载失败: {str(e)}")

    def map_clause(self, chunk) -> Dict:
        """保持原有接口，优化内部实现"""
        original_text = getattr(chunk, "original_text", "")
        return {
            "original_text": original_text,
            "clause": {
                "original_text": original_text,
                "summary": self._generate_summary(original_text),
                "obligations": self._extract_obligations(chunk),
                "law_references": self._extract_law_references(original_text)
            }
        }

    def _extract_law_references(self, text: str) -> List[str]:
        """增强法律条款识别"""
        patterns = [
            r"《([^》]+)》(第[零一二三四五六七八九十百]+条)",
            r"《([^》]+)》(?:的)?相关规定"
        ]
        laws = []
        for pattern in patterns:
            laws += [f"《{match[0]}》{match[1]}" if len(match) > 1 else f"《{match[0]}》"
                    for match in re.findall(pattern, text)]
        return list(set(laws))

    def _generate_summary(self, text: str) -> Optional[str]:
        if not self.summarizer or len(text) < 50:
            return None
        try:
            return self.summarizer(text, max_length=150)[0]['summary_text']
        except Exception as e:
            logging.error(f"摘要生成失败: {str(e)}")
            return None

    def _extract_obligations(self, chunk) -> List[Dict]:
        """兼容不同数据结构的实体输入"""
        entities = getattr(chunk, "entities", [])
        return [
            {"type": self.ENTITY_MAPPING.get(ent.label, "other"), "text": ent.text}
            for ent in entities
            if hasattr(ent, "label") and hasattr(ent, "text")
        ]