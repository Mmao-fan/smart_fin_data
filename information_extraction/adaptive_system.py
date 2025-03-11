from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import re
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np
from .schemas import Entity

@dataclass
class Pattern:
    type: str  # context, regex, keyword
    pattern: str
    entity_type: str
    weight: float = 1.0
    matches: int = 0
    success_rate: float = 0.0

class AdaptiveSystem:
    """自适应系统"""
    
    def __init__(self, data_dir: str = "data", patterns_file: str = "learned_patterns.json"):
        self.data_dir = Path(data_dir)
        self.patterns_file = self.data_dir / patterns_file
        self.patterns: List[Pattern] = []
        self.performance_history: List[Dict] = []
        self.load_patterns()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.patterns = {}  # 存储学习到的模式
        self.pattern_weights = {}  # 模式权重
        self.performance_metrics = {
            'processing_time': [],
            'enhancement_stats': {
                'original_counts': [],
                'enhanced_counts': []
            }
        }

    def load_patterns(self):
        """加载已学习的模式"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                self.patterns = [Pattern(**p) for p in patterns_data]
                self.logger.info(f"已加载 {len(self.patterns)} 个模式")
            except Exception as e:
                self.logger.error(f"加载模式文件时出错: {e}")
                self.patterns = []
    
    def save_patterns(self):
        """保存学习到的模式"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                patterns_data = [asdict(p) for p in self.patterns]
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存 {len(self.patterns)} 个模式")
        except Exception as e:
            self.logger.error(f"保存模式文件时出错: {e}")

    def learn_from_feedback(self, text: str, original_entities: List[Union[Dict, Entity]], corrected_entities: List[Union[Dict, Entity]]):
        """从用户反馈中学习"""
        self.logger.info("开始从反馈中学习...")
        
        # 转换实体为字典格式
        original_dicts = [self._entity_to_dict(e) for e in original_entities]
        corrected_dicts = [self._entity_to_dict(e) for e in corrected_entities]
        
        # 分析差异
        added_entities = []
        removed_entities = []
        modified_entities = []
        
        # 构建实体映射
        orig_map = {(e['start'], e['end']): e for e in original_dicts}
        corr_map = {(e['start'], e['end']): e for e in corrected_dicts}
        
        # 找出添加、删除和修改的实体
        for pos, entity in corr_map.items():
            if pos not in orig_map:
                added_entities.append(entity)
            elif orig_map[pos]['type'] != entity['type']:
                modified_entities.append((orig_map[pos], entity))
                
        for pos, entity in orig_map.items():
            if pos not in corr_map:
                removed_entities.append(entity)
        
        # 学习新模式
        for entity in added_entities:
            self._learn_new_patterns(text, entity)
        
        for orig, corr in modified_entities:
            self._update_pattern_weights(text, orig, corr)
            
        # 更新性能指标
        self._update_performance_metrics(original_dicts, corrected_dicts)
        
        # 保存更新后的模式
        self.save_patterns()
    
    def _entity_to_dict(self, entity: Union[Dict, Entity]) -> Dict:
        """将实体对象转换为字典"""
        if isinstance(entity, dict):
            return entity
        return {
            'type': entity.type,
            'text': entity.text,
            'start': entity.start,
            'end': entity.end
        }
        
    def _learn_new_patterns(self, text: str, entity: Dict):
        """学习新的模式"""
        # 提取上下文模式
        context_pattern = self._extract_context_pattern(text, entity)
        if context_pattern:
            self.patterns.append(Pattern(
                type="context",
                pattern=context_pattern,
                entity_type=entity['type']
            ))
            
        # 生成正则表达式模式
        regex_pattern = self._generate_regex_pattern(entity)
        if regex_pattern:
            self.patterns.append(Pattern(
                type="regex",
                pattern=regex_pattern,
                entity_type=entity['type']
            ))
            
        # 提取关键词模式
        keyword_pattern = self._extract_keyword_pattern(entity)
        if keyword_pattern:
            self.patterns.append(Pattern(
                type="keyword",
                pattern=keyword_pattern,
                entity_type=entity['type']
            ))

    def _extract_context_pattern(self, text: str, entity: Dict) -> Optional[str]:
        """提取上下文模式"""
        start, end = entity['start'], entity['end']
        context_before = text[max(0, start-20):start]
        context_after = text[end:min(len(text), end+20)]
        return f"{context_before}{{entity}}{context_after}"

    def _generate_regex_pattern(self, entity: Dict) -> Optional[str]:
        """生成正则表达式模式"""
        text = entity['text']
        if entity['type'] == 'ACCOUNT':
            return r'\d{16,19}'
        elif entity['type'] == 'MONEY':
            return r'\d+(\.\d{2})?元'
        return re.escape(text)

    def _extract_keyword_pattern(self, entity: Dict) -> Optional[str]:
        """提取关键词模式"""
        return entity['text']

    def _update_pattern_weights(self, text: str, original: Dict, corrected: Dict):
        """更新模式权重"""
        for pattern in self.patterns:
            if pattern.entity_type == original['type']:
                pattern.weight *= 0.9  # 降低错误模式的权重
            elif pattern.entity_type == corrected['type']:
                pattern.weight *= 1.1  # 提高正确模式的权重
                pattern.weight = min(pattern.weight, 2.0)  # 限制最大权重

    def enhance_recognition(self, text: str, entities: List[Entity]) -> List[Entity]:
        """增强实体识别"""
        enhanced_entities = entities.copy()
        
        # 应用已学习的模式
        for pattern, info in self.patterns.items():
            weight = self.pattern_weights.get(pattern, 0)
            if weight < 0.5:  # 忽略低权重模式
                continue
            
            if pattern in text:
                matches = re.finditer(re.escape(pattern), text)
                for match in matches:
                    start, end = match.span()
                    # 检查是否已存在相同实体
                    if not any(e.start == start and e.end == end for e in enhanced_entities):
                        enhanced_entities.append(Entity(
                            type=info['type'],
                            text=pattern,
                            start=start,
                            end=end
                        ))
        
        return enhanced_entities
    
    def _to_entity_object(self, entity: Union[Dict, Entity]) -> Entity:
        """将实体转换为Entity对象"""
        if isinstance(entity, Entity):
            return entity
        return Entity(
            type=entity['type'],
            text=entity['text'],
            start=entity['start'],
            end=entity['end']
        )

    def _has_overlap(self, entities: List[Entity], start: int, end: int) -> bool:
        """检查是否与现有实体重叠"""
        for entity in entities:
            if (start < entity.end and end > entity.start):
                return True
        return False

    def _update_performance_metrics(self, original_entities: List[Dict], corrected_entities: List[Dict]):
        """更新性能指标"""
        true_positives = len([e for e in original_entities if e in corrected_entities])
        false_positives = len(original_entities) - true_positives
        false_negatives = len(corrected_entities) - true_positives
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'pattern_count': len(self.patterns)
        }
        
        self.performance_history.append(metrics)
        self.logger.info(f"性能指标更新: {metrics}")

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.performance_history:
            return {
                'status': 'no_data',
                'message': '没有可用的性能数据'
            }
            
        latest = self.performance_history[-1]
        avg_metrics = {
            'precision': np.mean([m['precision'] for m in self.performance_history]),
            'recall': np.mean([m['recall'] for m in self.performance_history]),
            'f1': np.mean([m['f1'] for m in self.performance_history])
        }
        
        return {
            'status': 'success',
            'latest_metrics': latest,
            'average_metrics': avg_metrics,
            'pattern_count': len(self.patterns),
            'history_length': len(self.performance_history)
        }

    def update_patterns(self, text: str, entities: List[Dict[str, Any]]):
        """更新模式库"""
        for entity in entities:
            pattern = entity['text']
            if pattern not in self.patterns:
                self.patterns[pattern] = {
                    'type': entity['type'],
                    'count': 1,
                    'contexts': []
                }
                self.pattern_weights[pattern] = 1.0
            else:
                self.patterns[pattern]['count'] += 1
                self.pattern_weights[pattern] *= 1.1  # 增加权重
                
            # 提取上下文
            start = max(0, entity['start'] - 50)
            end = min(len(text), entity['end'] + 50)
            context = text[start:end]
            if context not in self.patterns[pattern]['contexts']:
                self.patterns[pattern]['contexts'].append(context)
                
    def get_learned_patterns(self) -> Dict[str, Any]:
        """获取已学习的模式"""
        return {
            pattern: {
                'type': info['type'],
                'weight': self.pattern_weights.get(pattern, 1.0),
                'count': info['count'],
                'contexts': info['contexts'][:3]  # 只返回前3个上下文示例
            }
            for pattern, info in self.patterns.items()
            if self.pattern_weights.get(pattern, 0) > 1.0  # 只返回权重大于1的模式
        }
        
    def update_enhancement_stats(self, original_count: int, enhanced_count: int):
        """更新增强效果统计"""
        self.performance_metrics['enhancement_stats']['original_counts'].append(original_count)
        self.performance_metrics['enhancement_stats']['enhanced_counts'].append(enhanced_count)
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'pattern_count': len(self.patterns),
            'high_weight_patterns': len([p for p, w in self.pattern_weights.items() if w > 1.5]),
            'average_weight': sum(self.pattern_weights.values()) / len(self.pattern_weights) if self.pattern_weights else 0,
            'enhancement_stats': {
                'total_enhancements': len(self.performance_metrics['enhancement_stats']['original_counts']),
                'average_improvement': (
                    sum(enhanced - original 
                        for original, enhanced 
                        in zip(self.performance_metrics['enhancement_stats']['original_counts'],
                             self.performance_metrics['enhancement_stats']['enhanced_counts']))
                    / len(self.performance_metrics['enhancement_stats']['original_counts'])
                    if self.performance_metrics['enhancement_stats']['original_counts']
                    else 0
                )
            }
        } 