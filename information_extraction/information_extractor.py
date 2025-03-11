# information_extraction/information_extractor.py
from typing import List, Dict, Any, Optional
import re
import logging
import uuid
from information_extraction.schemas import Entity, EntityLabel
from collections import defaultdict
from datetime import datetime

class InformationProcessor:
    """信息处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 实体识别模式
        self.entity_patterns = {
            EntityLabel.PERSON: [
                r'(?:[\u4e00-\u9fa5]{2,4}(?:先生|女士|老师|教授|董事长|总经理|经理|主任|员工))',
                r'(?:[A-Z][a-z]+\s+[A-Z][a-z]+)'
            ],
            EntityLabel.ORG: [
                r'(?:[\u4e00-\u9fa5]+(?:公司|集团|银行|企业|研究所|大学|学院|机构|部门))',
                r'(?:[A-Z][a-zA-Z\s]*(?:Corp|Inc|Ltd|LLC|Company|Group|Bank))'
            ],
            EntityLabel.MONEY: [
                r'(?:\d+(?:\.\d+)?(?:万|亿|千|百)?(?:元|美元|欧元|英镑|日元|人民币))',
                r'(?:USD|CNY|EUR|GBP|JPY)\s*\d+(?:\.\d+)?'
            ],
            EntityLabel.PERCENT: [
                r'\d+(?:\.\d+)?%',
                r'\d+(?:\.\d+)?个百分点'
            ],
            EntityLabel.DATE: [
                r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',
                r'\d{1,2}[-/月]\d{1,2}[日]?,?\s*\d{4}[年]?'
            ]
        }
        
        # 关系识别模式
        self.relation_patterns = {
            'acquisition': [
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?收购.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))',
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?并购.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))'
            ],
            'investment': [
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?投资.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))',
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?入股.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))'
            ],
            'cooperation': [
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?合作.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))',
                r'([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?签署.*?协议.*?([\u4e00-\u9fa5]+(?:公司|集团|企业))'
            ]
        }
        
        # 异常检测阈值
        self.anomaly_thresholds = {
            'money': {
                'min': 0,
                'max': 1e12  # 1万亿
            },
            'percent': {
                'min': 0,
                'max': 100
            }
        }
        
        # 处理统计
        self.statistics = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'total_entities': 0,
            'total_relations': 0,
            'total_anomalies': 0,
            'processing_time': defaultdict(float)
        }

    def process(self, text: str, file_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理文本"""
        if not text.strip():
            return {}
            
        try:
            self.statistics['total_processed'] += 1
            start_time = datetime.now()
            
            # 记录处理进度
            if file_info:
                self.logger.info(f"开始处理文件: {file_info.get('name', 'unknown')}")
                if file_info.get('total_pages'):
                    self.logger.info(f"总页数: {file_info['total_pages']}")
                if file_info.get('current_page'):
                    self.logger.info(f"当前处理页数: {file_info['current_page']}/{file_info['total_pages']}")
            
            # 提取实体
            entities = self.extract_entities(text)
            self.statistics['total_entities'] += len(entities)
            
            # 提取关系
            relations = self.extract_relations(text, entities)
            self.statistics['total_relations'] += len(relations)
            
            # 检测异常
            anomalies = self.detect_anomalies(entities)
            self.statistics['total_anomalies'] += len(anomalies)
            
            # 构建结果
            result = {
                'text': text,
                'entities': [e.__dict__ for e in entities],
                'relations': relations,
                'anomalies': anomalies,
                'metadata': {
                    'file_info': file_info,
                    'processing_time': (datetime.now() - start_time).total_seconds()
                }
            }
            
            # 更新统计信息
            self.statistics['successful_processed'] += 1
            self.statistics['processing_time'][file_info.get('name', 'unknown')] += result['metadata']['processing_time']
            
            # 记录处理结果
            self.logger.info(f"处理完成: 发现 {len(entities)} 个实体, {len(relations)} 个关系, {len(anomalies)} 个异常")
            if file_info and file_info.get('current_page') == file_info.get('total_pages'):
                self.logger.info(f"文件 {file_info['name']} 处理完成")
                self.logger.info(f"处理时间: {self.statistics['processing_time'][file_info['name']]:.2f} 秒")
            
            return result
            
        except Exception as e:
            self.statistics['failed_processed'] += 1
            self.logger.error(f"处理文本时出错: {str(e)}")
            return {
                'error': str(e),
                'text': text[:100] + '...' if len(text) > 100 else text,
                'metadata': {'file_info': file_info}
            }

    def extract_entities(self, text: str) -> List[Entity]:
        """提取实体"""
        entities = []
        
        try:
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, text):
                        entity = Entity(
                            id=str(uuid.uuid4()),
                            text=match.group(),
                            type=entity_type,
                            start=match.start(),
                            end=match.end(),
                            confidence=0.9  # 基于规则的匹配给予较高置信度
                        )
                        entities.append(entity)
            
            # 去重并按位置排序
            unique_entities = []
            seen = set()
            for entity in sorted(entities, key=lambda x: x.start):
                if entity.text not in seen:
                    seen.add(entity.text)
                    unique_entities.append(entity)
            
            return unique_entities
            
        except Exception as e:
            self.logger.error(f"实体提取失败: {str(e)}")
            return []

    def extract_relations(self, text: str, entities: List[Entity]) -> List[Dict[str, Any]]:
        """提取实体间的关系"""
        relations = []
        
        try:
            # 构建实体索引
            entity_index = defaultdict(list)
            for entity in entities:
                entity_index[entity.type].append(entity)
            
            # 使用模式匹配提取关系
            for relation_type, patterns in self.relation_patterns.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, text):
                        relation = {
                            'id': str(uuid.uuid4()),
                            'type': relation_type,
                            'source': match.group(1),
                            'target': match.group(2),
                            'text': match.group(),
                            'confidence': 0.8
                        }
                        relations.append(relation)
            
            return relations
            
        except Exception as e:
            self.logger.error(f"关系提取失败: {str(e)}")
            return []

    def detect_anomalies(self, entities: List[Entity]) -> List[Dict[str, Any]]:
        """检测异常值"""
        anomalies = []
        
        try:
            for entity in entities:
                if entity.type == EntityLabel.MONEY:
                    # 提取数值
                    try:
                        value = float(re.search(r'\d+(?:\.\d+)?', entity.text).group())
                        if value < self.anomaly_thresholds['money']['min'] or \
                           value > self.anomaly_thresholds['money']['max']:
                            anomalies.append({
                                'type': 'anomaly_money',
                                'entity_id': entity.id,
                                'value': value,
                                'text': entity.text,
                                'reason': '金额超出正常范围'
                            })
                    except:
                        pass
                        
                elif entity.type == EntityLabel.PERCENT:
                    try:
                        value = float(re.search(r'\d+(?:\.\d+)?', entity.text).group())
                        if value < self.anomaly_thresholds['percent']['min'] or \
                           value > self.anomaly_thresholds['percent']['max']:
                            anomalies.append({
                                'type': 'anomaly_percent',
                                'entity_id': entity.id,
                                'value': value,
                                'text': entity.text,
                                'reason': '百分比超出正常范围'
                            })
                    except:
                        pass
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'total_processed': self.statistics['total_processed'],
            'successful_processed': self.statistics['successful_processed'],
            'failed_processed': self.statistics['failed_processed'],
            'success_rate': self.statistics['successful_processed'] / max(1, self.statistics['total_processed']),
            'total_entities': self.statistics['total_entities'],
            'total_relations': self.statistics['total_relations'],
            'total_anomalies': self.statistics['total_anomalies'],
            'processing_time': dict(self.statistics['processing_time'])
        }