# relation_extractor.py
from typing import List, Dict, Any
from .schemas import (
    RelationType, 
    EntityLabel,
    Entity,
    Relation
)
import re


class FinancialRelationExtractor:
    """金融关系提取器"""
    
    def __init__(self):
        self.transfer_patterns = [
            r'(?:转账|汇款|支付|收款).*?(?:到|给|从)',
            r'(?:收到|接收).*?(?:从|由)',
            r'(?:转入|转出).*?(?:账户|卡)',
        ]
        
        self.ownership_patterns = [
            r'(?:属于|所有|持有|拥有)',
            r'(?:的账户|的卡|名下)',
            r'(?:法定代表人|实际控制人|受益人)'
        ]
        
        self.part_whole_patterns = [
            r'(?:子公司|分公司|分支机构|附属公司)',
            r'(?:隶属于|从属于|附属于)',
            r'(?:下属|旗下)'
        ]

    def find_transfer_relations(self, entities: List[Entity], text: str) -> List[Relation]:
        """查找转账关系"""
        relations = []
        
        # 提取账户相关实体
        accounts = [e for e in entities if e.type in [EntityLabel.ACCOUNT.value, EntityLabel.BANK.value]]
        amounts = [e for e in entities if e.type == EntityLabel.MONEY.value]
        dates = [e for e in entities if e.type == EntityLabel.DATE.value]
        
        # 对每个转账模式
        for pattern in self.transfer_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取转账描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                context_accounts = [
                    acc for acc in accounts 
                    if start <= acc.start <= end or start <= acc.end <= end
                ]
                context_amounts = [
                    amt for amt in amounts 
                    if start <= amt.start <= end or start <= amt.end <= end
                ]
                
                # 如果找到了账户和金额，创建转账关系
                if len(context_accounts) >= 2 and context_amounts:
                    source = context_accounts[0]
                    target = context_accounts[1]
                    amount = context_amounts[0]
                    
                    # 根据转账描述调整源和目标
                    if "收到" in context or "转入" in context:
                        source, target = target, source
                    
                    relations.append(Relation(
                        type=RelationType.TRANSFER_TO.value,
                        source=source,
                        target=target,
                        confidence=0.8
                    ))
        
        return relations

    def find_ownership_relations(self, entities: List[Entity], text: str) -> List[Relation]:
        """查找所有权关系"""
        relations = []
        
        # 提取相关实体
        persons = [e for e in entities if e.type == EntityLabel.PERSON.value]
        orgs = [e for e in entities if e.type == EntityLabel.ORG.value]
        accounts = [e for e in entities if e.type in [EntityLabel.ACCOUNT.value, EntityLabel.BANK.value]]
        
        # 对每个所有权模式
        for pattern in self.ownership_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                context_persons = [
                    p for p in persons 
                    if start <= p.start <= end or start <= p.end <= end
                ]
                context_orgs = [
                    o for o in orgs 
                    if start <= o.start <= end or start <= o.end <= end
                ]
                context_accounts = [
                    a for a in accounts 
                    if start <= a.start <= end or start <= a.end <= end
                ]
                
                # 创建所有权关系
                if context_persons and (context_orgs or context_accounts):
                    owner = context_persons[0]
                    owned = context_orgs[0] if context_orgs else context_accounts[0]
                    
                    relations.append(Relation(
                        type=RelationType.BELONGS_TO.value,
                        source=owned,
                        target=owner,
                        confidence=0.8
                    ))
        
        return relations

    def find_part_whole_relations(self, entities: List[Entity], text: str) -> List[Relation]:
        """查找部分-整体关系"""
        relations = []
        
        # 提取组织实体
        orgs = [e for e in entities if e.type == EntityLabel.ORG.value]
        
        # 对每个部分-整体模式
        for pattern in self.part_whole_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                context_orgs = [
                    o for o in orgs 
                    if start <= o.start <= end or start <= o.end <= end
                ]
                
                # 如果找到了多个组织实体，创建部分-整体关系
                if len(context_orgs) >= 2:
                    part = context_orgs[0]
                    whole = context_orgs[1]
                    
                    relations.append(Relation(
                        type=RelationType.PART_OF.value,
                        source=part,
                        target=whole,
                        confidence=0.8
                    ))
        
        return relations