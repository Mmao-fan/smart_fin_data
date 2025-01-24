# relation_extractor.py
from typing import List
from .schemas import EntityRelation, FinancialEntity


class FinancialRelationExtractor:
    @staticmethod
    def find_transfer_relations(entities: List[FinancialEntity], text: str) -> List[EntityRelation]:
        """识别转账关系：从A账户到B账户"""
        accounts = [e for e in entities if e.label == "ACCOUNT"]
        relations = []

        # 简单模式：邻近账户+关键词（如"transfer to"）
        for i in range(len(accounts) - 1):
            if "transfer" in text[accounts[i].end_pos:accounts[i + 1].start_pos].lower():
                relations.append(EntityRelation(
                    source=accounts[i],
                    target=accounts[i + 1],
                    relation_type="TRANSFER_TO"
                ))
        return relations