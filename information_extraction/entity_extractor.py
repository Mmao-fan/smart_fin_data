# entity_extractor.py
from typing import List, Dict, Any, Optional
import re
import logging
from enum import Enum
from .schemas import Entity

class EntityType(Enum):
    PERSON = "PERSON"
    ORG = "ORG"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    DATE = "DATE"
    TIME = "TIME"
    LOCATION = "LOCATION"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"

class FinancialEntityExtractor:
    """金融实体提取器"""
    
    def __init__(self):
        # 加载金融领域词典
        self.financial_terms = {
            "ORG": [
                "银行", "证券", "保险", "基金", "信托", "投资", "资产管理",
                "控股", "集团", "股份", "有限公司", "Bank", "Securities",
                "Insurance", "Fund", "Trust", "Investment", "Holdings"
            ],
            "EVENT": [
                "收购", "合并", "重组", "上市", "增发", "减持", "分红",
                "停牌", "复牌", "退市", "破产", "清算", "整改", "处罚"
            ],
            "PRODUCT": [
                "股票", "债券", "期货", "期权", "基金", "理财产品",
                "存单", "信托计划", "资管计划", "保单"
            ]
        }
        
        # 实体识别模式
        self.patterns = {
            "PERSON": r'(?:[\u4e00-\u9fa5]{2,4}(?:先生|女士|总经理|董事长|董事|监事|经理|主管|总监)|[A-Z][a-z]+\s+[A-Z][a-z]+)',
            "ORG": r'(?:[\u4e00-\u9fa5]{2,}(?:公司|银行|集团|企业|机构|部门|基金|商会|协会)|[A-Z][A-Za-z]+\s+(?:Inc\.|Corp\.|Ltd\.|LLC|Company|Bank|Group))',
            "MONEY": r'(?:(?:人民币|美元|欧元|日元|港币)?(?:\d+(?:\.\d+)?(?:万|亿|千|百|十)?元?)|(?:\$|€|￥|£)\d+(?:\.\d+)?[KMB]?)',
            "PERCENT": r'\d+(?:\.\d+)?%',
            "DATE": r'(?:\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?|\d{1,2}[-/月]\d{1,2}[日]?)',
            "TIME": r'(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)',
            "LOCATION": r'(?:[\u4e00-\u9fa5]{2,}(?:省|市|区|县|路|街|号|大厦|广场|中心)|[A-Z][a-z]+\s+(?:Street|Road|Avenue|Plaza|Center|Building))'
        }
        
        # 实体消歧规则
        self.disambiguation_rules = {
            "ORG": {
                "must_contain": ["公司", "银行", "集团", "Corp", "Inc", "Ltd"],
                "cannot_contain": ["先生", "女士", "Street", "Road"],
                "min_length": 4
            },
            "PERSON": {
                "must_contain": ["先生", "女士", "总经理", "董事"],
                "cannot_contain": ["公司", "银行", "集团"],
                "max_length": 8
            }
        }

    def extract_entities(self, text: str) -> List[Entity]:
        """提取实体"""
        entities = []
        
        # 使用正则模式提取基本实体
        for entity_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity = Entity(
                    type=entity_type,
                    text=match.group(),
                    start=match.start(),
                    end=match.end()
                )
                if self._validate_entity(entity):
                    entities.append(entity)
        
        # 使用金融词典增强识别
        for term_type, terms in self.financial_terms.items():
            for term in terms:
                matches = re.finditer(re.escape(term), text)
                for match in matches:
                    entity = Entity(
                        type=term_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end()
                    )
                    if self._validate_entity(entity):
                        entities.append(entity)
        
        # 实体消歧
        entities = self._disambiguate_entities(entities)
        
        # 合并重叠实体
        entities = self._merge_overlapping_entities(entities)
        
        # 按位置排序
        entities.sort(key=lambda x: x.start)
        
        return entities

    def _validate_entity(self, entity: Entity) -> bool:
        """验证实体有效性"""
        if entity.type not in self.disambiguation_rules:
            return True
            
        rules = self.disambiguation_rules[entity.type]
        text = entity.text
        
        # 检查必须包含的词
        if "must_contain" in rules:
            if not any(term in text for term in rules["must_contain"]):
                return False
                
        # 检查不能包含的词
        if "cannot_contain" in rules:
            if any(term in text for term in rules["cannot_contain"]):
                return False
                
        # 检查长度限制
        if "min_length" in rules and len(text) < rules["min_length"]:
            return False
        if "max_length" in rules and len(text) > rules["max_length"]:
            return False
            
        return True

    def _disambiguate_entities(self, entities: List[Entity]) -> List[Entity]:
        """实体消歧"""
        disambiguated = []
        context_window = 50  # 上下文窗口大小
        
        for i, entity in enumerate(entities):
            # 获取实体的上下文
            start = max(0, entity.start - context_window)
            end = min(entity.end + context_window, entity.end + 100)  # 假设文本长度足够
            
            # 根据上下文调整实体类型
            if entity.type == "ORG" and "先生" in entity.text:
                entity.type = "PERSON"
            elif entity.type == "PERSON" and any(term in entity.text for term in self.financial_terms["ORG"]):
                entity.type = "ORG"
                
            disambiguated.append(entity)
            
        return disambiguated

    def _merge_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并重叠实体"""
        if not entities:
            return []
            
        # 按开始位置排序
        entities.sort(key=lambda x: (x.start, -x.end))
        
        merged = []
        current = entities[0]
        
        for next_entity in entities[1:]:
            if current.end >= next_entity.start:
                # 如果实体重叠，选择更长的一个
                if next_entity.end - next_entity.start > current.end - current.start:
                    current = next_entity
            else:
                merged.append(current)
                current = next_entity
                
        merged.append(current)
        return merged

    def extract_key_info(self, text: str) -> Dict[str, List[str]]:
        """提取关键信息并按类型组织"""
        entities = self.extract_entities(text)
        
        # 按类型组织实体
        info = {}
        for entity in entities:
            if entity.type not in info:
                info[entity.type] = []
            if entity.text not in info[entity.type]:
                info[entity.type].append(entity.text)
        
        return info