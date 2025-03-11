# relation_extractor.py
from typing import List, Dict, Any
from .schemas import (
    EntityRelation, 
    FinancialEntity, 
    RelationType, 
    EntityLabel,
    Entity  # 添加Entity类的导入
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

    def find_transfer_relations(self, entities: List[Entity], text: str) -> List[Dict[str, Any]]:
        """查找转账关系"""
        relations = []
        
        # 提取账户相关实体
        accounts = [e for e in entities if e.label in [EntityLabel.ACCOUNT.value, EntityLabel.BANK.value]]
        amounts = [e for e in entities if e.label == EntityLabel.MONEY.value]
        dates = [e for e in entities if e.label == EntityLabel.DATE.value]
        
        # 对每个转账模式
        for pattern in self.transfer_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取转账描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                related_accounts = [
                    acc for acc in accounts 
                    if acc.end_pos >= start and acc.start_pos <= end
                ]
                related_amounts = [
                    amt for amt in amounts 
                    if amt.start >= start and amt.end <= end
                ]
                related_dates = [
                    dt for dt in dates 
                    if dt.start >= start and dt.end <= end
                ]
                
                # 如果找到相关实体，创建关系
                if len(related_accounts) >= 2 and related_amounts:
                    relation = {
                        'type': RelationType.TRANSFER_TO.value,
                        'source': {
                            'type': related_accounts[0].label,
                            'text': related_accounts[0].text
                        },
                        'target': {
                            'type': related_accounts[1].label,
                            'text': related_accounts[1].text
                        },
                        'amount': {
                            'text': related_amounts[0].text
                        },
                        'date': related_dates[0].text if related_dates else None,
                        'context': context,
                        'confidence': 0.9
                    }
                    relations.append(relation)
                
                # 处理单向转账（只有一个账户实体）
                elif len(related_accounts) == 1 and related_amounts:
                    # 判断是转入还是转出
                    is_transfer_in = any(word in context for word in ['收到', '转入', '收款'])
                    relation = {
                        'type': RelationType.TRANSFER_TO.value if not is_transfer_in else RelationType.BELONGS_TO.value,
                        'source': {
                            'type': related_accounts[0].label,
                            'text': related_accounts[0].text
                        },
                        'amount': {
                            'text': related_amounts[0].text
                        },
                        'date': related_dates[0].text if related_dates else None,
                        'context': context,
                        'confidence': 0.7
                    }
                    relations.append(relation)
        
        return relations

    def find_ownership_relations(self, entities: List[Entity], text: str) -> List[Dict[str, Any]]:
        """查找所有权关系"""
        relations = []
        
        # 提取相关实体
        orgs = [e for e in entities if e.label == EntityLabel.ORG.value]
        persons = [e for e in entities if e.label == EntityLabel.PERSON.value]
        products = [e for e in entities if e.label == EntityLabel.PRODUCT.value]
        
        # 对每个所有权模式
        for pattern in self.ownership_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                related_orgs = [org for org in orgs if org.start >= start and org.end <= end]
                related_persons = [person for person in persons if person.start >= start and person.end <= end]
                related_products = [prod for prod in products if prod.start >= start and prod.end <= end]
                
                # 创建组织-人员关系
                for org in related_orgs:
                    for person in related_persons:
                        relation = {
                            'type': RelationType.BELONGS_TO.value,
                            'source': {
                                'type': person.label,
                                'text': person.text
                            },
                            'target': {
                                'type': org.label,
                                'text': org.text
                            },
                            'context': context,
                            'confidence': 0.8
                        }
                        relations.append(relation)
                
                # 创建组织-产品关系
                for org in related_orgs:
                    for product in related_products:
                        relation = {
                            'type': RelationType.OWNS.value,
                            'source': {
                                'type': org.label,
                                'text': org.text
                            },
                            'target': {
                                'type': product.label,
                                'text': product.text
                            },
                            'context': context,
                            'confidence': 0.8
                        }
                        relations.append(relation)
        
        return relations

    def find_part_whole_relations(self, entities: List[Entity], text: str) -> List[Dict[str, Any]]:
        """查找部分-整体关系"""
        relations = []
        
        # 提取相关实体
        orgs = [e for e in entities if e.label == EntityLabel.ORG.value]
        departments = [e for e in entities if e.label == EntityLabel.DEPARTMENT.value]
        
        # 对每个部分-整体模式
        for pattern in self.part_whole_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 获取描述的上下文
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 在上下文中查找相关实体
                related_orgs = [org for org in orgs if org.start >= start and org.end <= end]
                related_departments = [dept for dept in departments if dept.start >= start and dept.end <= end]
                
                # 创建部门-组织关系
                for org in related_orgs:
                    for department in related_departments:
                        relation = {
                            'type': RelationType.PART_OF.value,
                            'source': {
                                'type': department.label,
                                'text': department.text
                            },
                            'target': {
                                'type': org.label,
                                'text': org.text
                            },
                            'context': context,
                            'confidence': 0.8
                        }
                        relations.append(relation)
        
        return relations