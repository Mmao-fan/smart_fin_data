# entity_extractor.py
import re
import spacy
from typing import List
from .schemas import FinancialEntity


class FinancialEntityExtractor:
    def __init__(self):
        # 加载模型时禁用不需要的组件
        self.nlp = spacy.load("en_core_web_lg", disable=["parser", "lemmatizer"])
        self._add_patterns()

    def _add_patterns(self):
        # 创建 EntityRuler 并添加到管道
        ruler = self.nlp.add_pipe("entity_ruler")

        # 定义金融正则模式
        patterns = [
            {
                "label": "MONEY",
                "pattern": [
                    {"TEXT": {"REGEX": "^\$?[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?$"}}
                ]
            },
            {
                "label": "SWIFT_CODE",
                "pattern": [
                    {"TEXT": {"REGEX": "^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"}}
                ]
            }
        ]

        # 添加模式到实体规则器
        ruler.add_patterns(patterns)

    def extract_entities(self, text: str) -> List[FinancialEntity]:
        doc = self.nlp(text)
        entities = []

        # 提取 spaCy 识别的实体
        for ent in doc.ents:
            entities.append(FinancialEntity(
                text=ent.text,
                label=ent.label_,
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                confidence=0.9
            ))

        # 补充正则提取（例如信用卡号）
        for match in re.finditer(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", text):
            entities.append(FinancialEntity(
                text=match.group(),
                label="CREDIT_CARD",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=1.0
            ))

        return entities