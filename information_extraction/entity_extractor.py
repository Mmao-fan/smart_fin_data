# entity_extractor.py
import re
import spacy
from typing import List
from .schemas import FinancialEntity, EntityLabel

class FinancialEntityExtractor:
    def __init__(self):
        # 加载模型时明确启用 "entity_ruler" 组件
        self.nlp = spacy.load("en_core_web_lg", disable=["parser", "lemmatizer"])
        self._add_entity_ruler()  # 重命名方法以明确功能

    def _add_entity_ruler(self):
        """创建 EntityRuler 并添加正则规则"""
        ruler = self.nlp.add_pipe("entity_ruler")
        patterns = [
            {
                "label": EntityLabel.MONEY.value,
                "pattern": [{
                    "TEXT": {"REGEX": r"^\$?[0-9,]+(?:\.\d{1,2})?(?: million| billion)?$"}
                }]
            },
            {
                "label": EntityLabel.SWIFT_CODE.value,
                "pattern": [{
                    "TEXT": {"REGEX": r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"}
                }]
            }
        ]
        ruler.add_patterns(patterns)  # 正确调用 add_patterns 方法

    def extract_entities(self, text: str) -> List[FinancialEntity]:
        doc = self.nlp(text)
        entities = []
        seen = set()

        # 使用正确的 start_char 和 end_char 属性
        for ent in doc.ents:
            key = (ent.text, ent.start_char, ent.end_char)  # 使用 spaCy 的 start_char/end_char
            if key not in seen:
                try:
                    label = EntityLabel(ent.label_)
                except ValueError:
                    continue
                entities.append(FinancialEntity(
                    text=ent.text,
                    label=label,
                    start_pos=ent.start_char,  # 正确属性名
                    end_pos=ent.end_char,       # 正确属性名
                    confidence=0.9
                ))
                seen.add(key)

        # 正则提取信用卡号
        for match in re.finditer(r"\b(?:\d{4}[- ]?){3}\d{4}\b", text):
            entities.append(FinancialEntity(
                text=match.group(),
                label=EntityLabel.CREDIT_CARD,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=1.0
            ))
        return entities