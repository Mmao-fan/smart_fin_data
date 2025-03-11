# information_extraction/information_extractor.py
from typing import List, Dict, Any, Optional
import re
import logging
from collections import defaultdict
import time

from .entity_extractor import FinancialEntityExtractor
from .relation_extractor import FinancialRelationExtractor
from .anomaly_detector import FraudDetector
from .summarizer import ComplianceSummarizer
from .qa_generator import QAPairGenerator
from .compliance_detector import ComplianceDetector
from .privacy_protector import SensitiveInfoDetector, DataAnonymizer
from .schemas import ProcessedChunk, Entity, ComplianceEvent
from .entity_extractor import EntityExtractor
from .adaptive_learning import AdaptiveLearningManager

class InformationProcessor:
    """信息处理器"""
    
    def __init__(self, enable_privacy_protection: bool = True, adaptive_learning: bool = True):
        self.entity_extractor = FinancialEntityExtractor()
        self.relation_extractor = FinancialRelationExtractor()
        self.anomaly_detector = FraudDetector()
        self.summarizer = ComplianceSummarizer()
        self.qa_generator = QAPairGenerator()
        self.compliance_detector = ComplianceDetector()
        self.enable_privacy_protection = enable_privacy_protection
        self.adaptive_learning = adaptive_learning
        
        if enable_privacy_protection:
            self.sensitive_detector = SensitiveInfoDetector()
            self.anonymizer = DataAnonymizer(self.sensitive_detector)
        
        if adaptive_learning:
            self.learning_manager = AdaptiveLearningManager()

    def process_chunk(self, chunk_id: int, text: str, scenario: str = None) -> Optional[ProcessedChunk]:
        """处理文本块"""
        if not text.strip():
            return None
            
        try:
            start_time = time.time()
            
            # 1. 提取实体
            entities = self.entity_extractor.extract_entities(text)
            
            # 如果启用了自适应学习，应用学习到的模式
            if self.adaptive_learning:
                entities = self._apply_learned_patterns(text, entities)
            
            # 2. 提取关系
            relations = self.relation_extractor.find_transfer_relations(entities, text)
            relations.extend(self.relation_extractor.find_ownership_relations(entities, text))
            relations.extend(self.relation_extractor.find_part_whole_relations(entities, text))
            
            processing_time = time.time() - start_time
            
            # 3. 检测异常
            anomalies = self.anomaly_detector.detect_time_anomalies(entities, text)
            
            # 4. 检测合规事件
            compliance_events = self.compliance_detector.detect_compliance_events(text)
            
            # 5. 生成摘要
            summary = None
            if len(text) > 100:  # 只对较长文本生成摘要
                summary = self.summarizer.summarize_regulation(text)
            
            # 6. 生成问答对
            qa_pairs = None
            if scenario:
                qa_pairs = self.qa_generator.generate_qa_pairs(text, scenario)
            
            # 7. 合规风险分析
            compliance_analysis = None
            if compliance_events:
                compliance_analysis = self.compliance_detector.analyze_compliance_risk(compliance_events)
            
            # 创建处理后的文本块
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                original_text=text,
                entities=entities,
                relations=relations,
                summary=summary,
                anomalies=anomalies,
                qa_pairs=qa_pairs,
                compliance_events=compliance_events,
                compliance_analysis=compliance_analysis
            )
            
            # 如果启用了隐私保护，对结果进行脱敏处理
            if self.enable_privacy_protection:
                processed_chunk = self._anonymize_processed_chunk(processed_chunk)
            
            # 如果启用了自适应学习，记录处理时间
            if self.adaptive_learning:
                self._record_processing_time(processing_time)
            
            return processed_chunk
            
        except Exception as e:
            logging.error(f"处理文本块失败: {str(e)}", exc_info=True)
            return None

    def extract_key_info(self, text: str) -> Dict[str, Any]:
        """提取关键信息"""
        try:
            # 1. 基础实体提取
            entities = self.entity_extractor.extract_entities(text)
            
            # 2. 按类型组织实体
            info = defaultdict(list)
            for entity in entities:
                if entity.text not in info[entity.type]:
                    info[entity.type].append(entity.text)
            
            # 3. 提取合规事件
            compliance_events = self.compliance_detector.detect_compliance_events(text)
            if compliance_events:
                info["COMPLIANCE_EVENTS"] = [
                    {
                        "type": event.type,
                        "text": event.text,
                        "importance": event.importance
                    }
                    for event in compliance_events
                ]
            
            # 4. 检测异常
            anomalies = self.anomaly_detector.detect_time_anomalies(entities, text)
            if anomalies:
                info["ANOMALIES"] = [
                    {
                        "type": anomaly.type,
                        "description": anomaly.description,
                        "confidence": anomaly.confidence
                    }
                    for anomaly in anomalies
                ]
            
            # 5. 生成摘要
            if len(text) > 100:
                summary = self.summarizer.summarize_regulation(text)
                if summary:
                    info["SUMMARY"] = summary
            
            return dict(info)
            
        except Exception as e:
            logging.error(f"提取关键信息失败: {str(e)}", exc_info=True)
            return {}

    def _anonymize_processed_chunk(self, chunk: ProcessedChunk) -> ProcessedChunk:
        """对处理后的文本块进行脱敏处理"""
        if not self.enable_privacy_protection:
            return chunk
            
        try:
            # 检测敏感信息
            sensitive_info = self.sensitive_detector.detect_sensitive_info(chunk.original_text)
            
            # 对文本进行脱敏处理
            anonymized_text = self.anonymizer.anonymize_text(chunk.original_text, sensitive_info)
            
            # 更新处理后的文本块
            chunk.original_text = anonymized_text
            
            # 对摘要进行脱敏处理
            if chunk.summary:
                sensitive_info_summary = self.sensitive_detector.detect_sensitive_info(chunk.summary)
                chunk.summary = self.anonymizer.anonymize_text(chunk.summary, sensitive_info_summary)
            
            # 对问答对进行脱敏处理
            if chunk.qa_pairs:
                for qa_pair in chunk.qa_pairs:
                    sensitive_info_q = self.sensitive_detector.detect_sensitive_info(qa_pair["question"])
                    sensitive_info_a = self.sensitive_detector.detect_sensitive_info(qa_pair["answer"])
                    
                    qa_pair["question"] = self.anonymizer.anonymize_text(qa_pair["question"], sensitive_info_q)
                    qa_pair["answer"] = self.anonymizer.anonymize_text(qa_pair["answer"], sensitive_info_a)
            
            return chunk
            
        except Exception as e:
            logging.error(f"文本脱敏处理失败: {str(e)}", exc_info=True)
            return chunk

    def extract_training_data(self, text: str, scenario: str) -> Dict[str, Any]:
        """提取适合模型训练的数据"""
        try:
            # 1. 提取实体
            entities = self.entity_extractor.extract_entities(text)
            
            # 2. 提取关系
            relations = self.relation_extractor.find_transfer_relations(entities, text)
            
            # 3. 检测合规事件
            compliance_events = self.compliance_detector.detect_compliance_events(text)
            
            # 4. 生成问答对
            qa_pairs = []
            if scenario:
                qa_pairs = self.qa_generator.generate_qa_pairs(text, scenario)
            
            # 5. 生成摘要
            summary = None
            if len(text) > 100:
                summary = self.summarizer.summarize_regulation(text)
            
            # 6. 合规风险分析
            compliance_analysis = None
            if compliance_events:
                compliance_analysis = self.compliance_detector.analyze_compliance_risk(compliance_events)
            
            # 构建训练数据
            training_data = {
                'scenario': scenario,
                'qa_pairs': qa_pairs or [],
                'entities': [
                    {
                        'type': entity.type,
                        'text': entity.text,
                        'start': entity.start,
                        'end': entity.end
                    }
                    for entity in entities
                ],
                'relations': relations,
                'summary': summary,
                'compliance_events': [
                    {
                        'type': event.type,
                        'text': event.text,
                        'importance': event.importance,
                        'subtype': event.subtype
                    }
                    for event in (compliance_events or [])
                ],
                'compliance_analysis': compliance_analysis,
                'metadata': {
                    'text_length': len(text),
                    'entity_count': len(entities),
                    'relation_count': len(relations),
                    'qa_pair_count': len(qa_pairs) if qa_pairs else 0,
                    'has_summary': summary is not None,
                    'compliance_event_count': len(compliance_events) if compliance_events else 0
                }
            }
            
            return training_data
            
        except Exception as e:
            logging.error(f"提取训练数据失败: {str(e)}", exc_info=True)
            return {
                'scenario': scenario,
                'qa_pairs': [],
                'entities': [],
                'relations': [],
                'summary': None,
                'compliance_events': [],
                'compliance_analysis': None,
                'metadata': {
                    'error': str(e)
                }
            }

    def _apply_learned_patterns(self, text: str, entities: List[Entity]) -> List[Entity]:
        """应用学习到的模式"""
        if not self.adaptive_learning:
            return entities
        
        patterns = self.learning_manager.get_learned_patterns()
        enhanced_entities = entities.copy()
        
        for pattern_key, pattern in patterns.items():
            if pattern['text'] in text and pattern['weight'] > 1.0:
                # 查找模式匹配
                start = text.find(pattern['text'])
                if start != -1:
                    end = start + len(pattern['text'])
                    # 检查是否已存在相同实体
                    exists = any(e.start == start and e.end == end 
                               for e in enhanced_entities)
                    if not exists:
                        enhanced_entities.append(Entity(
                            type=pattern['type'],
                            text=pattern['text'],
                            start=start,
                            end=end
                        ))
        
        return enhanced_entities
    
    def _record_processing_time(self, processing_time: float):
        """记录处理时间"""
        if self.adaptive_learning:
            self.learning_manager.performance_metrics['processing_time'].append(
                processing_time
            )
    
    def update_from_feedback(self, 
                           text: str,
                           original_entities: List[Entity],
                           corrected_entities: List[Entity]):
        """根据用户反馈更新系统"""
        if not self.adaptive_learning:
            return
        
        processing_time = time.time()  # 模拟处理时间
        self.learning_manager.update_from_feedback(
            text,
            original_entities,
            corrected_entities,
            processing_time
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.adaptive_learning:
            return {'status': 'Adaptive learning is disabled'}
        return self.learning_manager.get_performance_report()