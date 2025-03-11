# adaptive_learning.py
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional
import json
import logging
from pathlib import Path
import numpy as np
from .schemas import Entity, EntityLabel, RelationType

logger = logging.getLogger(__name__)

class AdaptiveLearningManager:
    """自适应学习管理器"""
    def __init__(self, data_dir: str = "data/adaptive_learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载或初始化学习数据
        self.pattern_weights = self._load_json("pattern_weights.json", default={})
        self.feedback_history = self._load_json("feedback_history.json", default=[])
        self.entity_patterns = self._load_json("entity_patterns.json", default={})
        
        # 性能指标跟踪
        self.performance_metrics = {
            'entity_accuracy': [],
            'relation_accuracy': [],
            'processing_time': []
        }
        
    def _load_json(self, filename: str, default: Any = None) -> Any:
        """加载JSON文件，如果不存在则返回默认值"""
        file_path = self.data_dir / filename
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {filename}: {e}")
        return default
    
    def _save_json(self, data: Any, filename: str):
        """保存数据到JSON文件"""
        try:
            with open(self.data_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
    
    def update_from_feedback(self, 
                           text: str, 
                           original_entities: List[Entity],
                           corrected_entities: List[Entity],
                           processing_time: float):
        """根据反馈更新学习数据"""
        # 记录反馈
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'text': text,
            'original_entities': [self._entity_to_dict(e) for e in original_entities],
            'corrected_entities': [self._entity_to_dict(e) for e in corrected_entities],
            'processing_time': processing_time
        }
        self.feedback_history.append(feedback_entry)
        
        # 更新性能指标
        accuracy = self._calculate_accuracy(original_entities, corrected_entities)
        self.performance_metrics['entity_accuracy'].append(accuracy)
        self.performance_metrics['processing_time'].append(processing_time)
        
        # 学习新模式
        self._learn_new_patterns(text, corrected_entities)
        
        # 保存更新后的数据
        self._save_learning_data()
    
    def _entity_to_dict(self, entity: Entity) -> Dict:
        """将实体对象转换为字典"""
        return {
            'type': entity.type,
            'text': entity.text,
            'start': entity.start,
            'end': entity.end
        }
    
    def _calculate_accuracy(self, 
                          original: List[Entity], 
                          corrected: List[Entity]) -> float:
        """计算实体识别准确率"""
        if not corrected:
            return 1.0 if not original else 0.0
        
        correct_count = sum(1 for o in original 
                          if any(c.text == o.text and c.type == o.type 
                                for c in corrected))
        return correct_count / len(corrected)
    
    def _learn_new_patterns(self, text: str, entities: List[Entity]):
        """学习新的实体模式"""
        for entity in entities:
            # 提取实体上下文
            context_start = max(0, entity.start - 20)
            context_end = min(len(text), entity.end + 20)
            context = text[context_start:context_end]
            
            # 生成模式
            pattern = {
                'text': entity.text,
                'type': entity.type,
                'context': context,
                'weight': 1.0
            }
            
            # 更新模式库
            pattern_key = f"{entity.type}_{context}"
            if pattern_key not in self.entity_patterns:
                self.entity_patterns[pattern_key] = pattern
            else:
                self.entity_patterns[pattern_key]['weight'] *= 1.1
    
    def _save_learning_data(self):
        """保存学习数据"""
        self._save_json(self.pattern_weights, "pattern_weights.json")
        self._save_json(self.feedback_history, "feedback_history.json")
        self._save_json(self.entity_patterns, "entity_patterns.json")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.performance_metrics['entity_accuracy']:
            return {'status': 'No data available'}
        
        recent_accuracy = self.performance_metrics['entity_accuracy'][-100:]
        recent_time = self.performance_metrics['processing_time'][-100:]
        
        return {
            'average_accuracy': np.mean(recent_accuracy),
            'accuracy_trend': np.polyfit(range(len(recent_accuracy)), recent_accuracy, 1)[0],
            'average_processing_time': np.mean(recent_time),
            'total_patterns_learned': len(self.entity_patterns),
            'feedback_count': len(self.feedback_history)
        }
    
    def get_learned_patterns(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """获取学习到的模式"""
        if entity_type:
            return {k: v for k, v in self.entity_patterns.items() 
                   if v['type'] == entity_type}
        return self.entity_patterns 