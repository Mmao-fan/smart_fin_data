# relation_extractor.py
from typing import List, Dict, Any, Optional
from .schemas import (
    RelationType, 
    EntityLabel,
    Entity,
    Relation
)
import re
import logging
import uuid


class RelationExtractor:
    """关系提取器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 定义关系模式
        self.relation_patterns = {
            'transfer': [
                r'(?P<source>[\w\s]+)向(?P<target>[\w\s]+)转账(?P<amount>[\d\.]+(?:万|亿)?元)',
                r'(?P<source>[\w\s]+)支付(?P<target>[\w\s]+)(?P<amount>[\d\.]+(?:万|亿)?元)',
            ],
            'ownership': [
                r'(?P<source>[\w\s]+)持有(?P<target>[\w\s]+)(?P<percentage>[\d\.]+%)股份',
                r'(?P<source>[\w\s]+)是(?P<target>[\w\s]+)的控股股东',
            ],
            'investment': [
                r'(?P<source>[\w\s]+)投资(?P<target>[\w\s]+)(?P<amount>[\d\.]+(?:万|亿)?元)',
                r'(?P<source>[\w\s]+)认购(?P<target>[\w\s]+)(?P<amount>[\d\.]+(?:万|亿)?元)',
            ],
            'cooperation': [
                r'(?P<source>[\w\s]+)与(?P<target>[\w\s]+)签署(?:合作|协议)',
                r'(?P<source>[\w\s]+)和(?P<target>[\w\s]+)达成(?:合作|协议)',
            ],
            'employment': [
                r'(?P<source>[\w\s]+)担任(?P<target>[\w\s]+)(?P<position>[\w\s]+职务)',
                r'(?P<source>[\w\s]+)是(?P<target>[\w\s]+)的(?P<position>[\w\s]+)',
            ]
        }

    def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """提取实体间的关系"""
        try:
            relations = []
            
            # 基于规则的关系提取
            for rel_type, patterns in self.relation_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        source_text = match.group('source').strip()
                        target_text = match.group('target').strip()
                        
                        source_entity = self._find_closest_entity(source_text, entities)
                        target_entity = self._find_closest_entity(target_text, entities)
                        
                        if source_entity and target_entity:
                            relation = Relation(
                                id=str(uuid.uuid4()),
                                type=rel_type,
                                source=source_entity,
                                target=target_entity,
                                confidence=0.8,
                                metadata={
                                    'pattern': pattern,
                                    'match_text': match.group(0)
                                }
                            )
                            relations.append(relation)
            
            # 基于共现的关系提取
            cooccurrence_relations = self._extract_cooccurrence_relations(text, entities)
            relations.extend(cooccurrence_relations)
            
            # 合并相似的关系
            relations = self._merge_similar_relations(relations)
            
            return relations
            
        except Exception as e:
            self.logger.error(f"关系提取失败: {str(e)}")
            return []

    def _find_closest_entity(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """找到最接近的实体"""
        best_match = None
        best_score = 0
        
        for entity in entities:
            score = self._calculate_text_similarity(text, entity.text)
            if score > best_score and score > 0.6:  # 设置阈值
                best_score = score
                best_match = entity
        
        return best_match

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 使用简单的字符重叠率
        chars1 = set(text1)
        chars2 = set(text2)
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        return intersection / union if union > 0 else 0

    def _extract_cooccurrence_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """提取基于共现的关系"""
        relations = []
        
        # 将文本分成句子
        sentences = re.split(r'[。！？!?]', text)
        
        for sentence in sentences:
            sentence_entities = [
                e for e in entities
                if e.start >= text.find(sentence) and
                e.end <= text.find(sentence) + len(sentence)
            ]
            
            # 检查每对实体
            for i, e1 in enumerate(sentence_entities):
                for e2 in sentence_entities[i+1:]:
                    rel_type = self._infer_relation_type(e1, e2, sentence)
                    if rel_type:
                        relation = Relation(
                            id=str(uuid.uuid4()),
                            type=rel_type,
                            source=e1,
                            target=e2,
                            confidence=0.6,
                            metadata={
                                'method': 'cooccurrence',
                                'sentence': sentence
                            }
                        )
                        relations.append(relation)
        
        return relations

    def _infer_relation_type(self, e1: Entity, e2: Entity, context: str) -> Optional[str]:
        """推断两个实体之间的关系类型"""
        # 基于实体类型和上下文推断关系
        if e1.type == 'PERSON' and e2.type == 'ORG':
            if any(word in context for word in ['担任', '任职', '就职']):
                return 'employment'
            elif any(word in context for word in ['投资', '认购']):
                return 'investment'
        elif e1.type == 'ORG' and e2.type == 'ORG':
            if any(word in context for word in ['收购', '持股', '控股']):
                return 'ownership'
            elif any(word in context for word in ['合作', '协议', '签署']):
                return 'cooperation'
        
        return None

    def _merge_similar_relations(self, relations: List[Relation]) -> List[Relation]:
        """合并相似的关系"""
        merged = []
        used = set()
        
        for i, r1 in enumerate(relations):
            if i in used:
                continue
                
            similar = [r1]
            used.add(i)
            
            # 查找相似的关系
            for j, r2 in enumerate(relations[i+1:], i+1):
                if j not in used and self._are_relations_similar(r1, r2):
                    similar.append(r2)
                    used.add(j)
            
            # 如果找到相似关系，选择置信度最高的
            if similar:
                best_relation = max(similar, key=lambda r: r.confidence)
                merged.append(best_relation)
        
        return merged

    def _are_relations_similar(self, r1: Relation, r2: Relation) -> bool:
        """判断两个关系是否相似"""
        return (
            r1.type == r2.type and
            self._calculate_text_similarity(r1.source.text, r2.source.text) > 0.8 and
            self._calculate_text_similarity(r1.target.text, r2.target.text) > 0.8
        )