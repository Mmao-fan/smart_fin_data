# relation_extractor.py
from typing import List
from .schemas import EntityRelation, FinancialEntity, RelationType, EntityLabel  # 添加 EntityLabel 导入
import re


class FinancialRelationExtractor:
    @staticmethod
    def find_transfer_relations(
            entities: List[FinancialEntity],
            text: str
    ) -> List[EntityRelation]:
        """识别转账关系（严格使用枚举类型）"""
        accounts = [e for e in entities if e.label == EntityLabel.ACCOUNT]  # 使用 EntityLabel.ACCOUNT
        relations = []
        transfer_keywords = r"(transfer|sent|remitted|to|->|→)"

        for i in range(len(accounts)):
            for j in range(i + 1, len(accounts)):
                start = accounts[i].end_pos
                end = accounts[j].start_pos
                context = text[start:end]
                if re.search(transfer_keywords, context, re.IGNORECASE):
                    relations.append(EntityRelation(
                        source=accounts[i],
                        target=accounts[j],
                        relation_type=RelationType.TRANSFER_TO
                    ))
        return relations