# -*- coding: utf-8 -*-
from typing import List, Dict, Any
import logging
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict
import re

class EnhancedAdaptiveSystem:
    """增强自适应系统"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = defaultdict(list)  # 学习到的模式
        self.keywords = defaultdict(set)  # 学习到的关键词
        self.scene_patterns = defaultdict(list)  # 场景特定模式
        self.statistics = {
            'texts_processed': 0,
            'patterns_learned': 0,
            'keywords_learned': 0,
            'entities_enhanced': 0,
            'scenes_detected': defaultdict(int),
            'pattern_effectiveness': defaultdict(lambda: {'matches': 0, 'total': 0})
        }
        
        # 初始化高级模式
        self._init_advanced_patterns()
        self._init_scene_patterns()
        
    def _init_advanced_patterns(self):
        """初始化高级模式"""
        self.patterns['company'] = [
            r'(?:[\u4e00-\u9fa5]+(?:公司|集团|企业|银行))',
            r'(?:[A-Z][a-zA-Z\s]*(?:Corp|Inc|Ltd|LLC|Company|Group|Bank))'
        ]
        self.patterns['money'] = [
            r'(?:\d+(?:\.\d+)?(?:万|亿|千|百)?(?:元|美元|欧元|英镑|日元|人民币))',
            r'(?:USD|CNY|EUR|GBP|JPY)\s*\d+(?:\.\d+)?'
        ]
        self.patterns['date'] = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',
            r'\d{1,2}[-/月]\d{1,2}[日]?,?\s*\d{4}[年]?'
        ]
        self.patterns['person'] = [
            r'(?:[\u4e00-\u9fa5]{2,4}(?:先生|女士|老师|教授|董事长|总经理|经理|主任))',
            r'(?:[A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]

    def _init_scene_patterns(self):
        """初始化场景特定模式"""
        self.scene_patterns['acquisition'] = {
            'indicators': [
                r'收购|并购|重组|控股|入股',
                r'股权|股份|控制权'
            ],
            'patterns': {
                'target': r'(?:收购|并购|获得).*?([\u4e00-\u9fa5]+(?:公司|集团|企业)).*?(?:\d+%|全部)?股权',
                'amount': r'(?:交易金额|对价|收购价格).*?(\d+(?:\.\d+)?(?:万|亿)?(?:元|美元|欧元))',
                'stake': r'(?:持股比例|股权占比).*?(\d+(?:\.\d+)?%)'
            }
        }
        self.scene_patterns['financial_report'] = {
            'indicators': [
                r'财报|业绩|报表',
                r'营收|利润|净利'
            ],
            'patterns': {
                'revenue': r'营业收入.*?(\d+(?:\.\d+)?(?:万|亿)?元)',
                'profit': r'净利润.*?(\d+(?:\.\d+)?(?:万|亿)?元)',
                'growth': r'同比增长.*?(\d+(?:\.\d+)?%)'
            }
        }

    def process(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理文本，应用学习到的模式和关键词"""
        if not text:
            return {'text': text, 'enhancements': []}
            
        try:
            # 更新统计信息
            self.statistics['texts_processed'] += 1
            
            # 检测文本场景
            scene_info = self._detect_scene(text)
            if scene_info['scene']:
                self.statistics['scenes_detected'][scene_info['scene']] += 1
                self.logger.info(f"检测到场景: {scene_info['scene']}, 置信度: {scene_info['confidence']:.2f}")
            
            # 应用场景特定模式
            scene_entities = self._apply_scene_patterns(text, scene_info['scene']) if scene_info['scene'] else []
            
            # 应用通用模式
            enhanced_text = text
            general_entities = []
            for pattern_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        self.statistics['patterns_learned'] += 1
                        entity = match.group()
                        general_entities.append({
                            'type': pattern_type,
                            'text': entity,
                            'start': match.start(),
                            'end': match.end()
                        })
                        enhanced_text = enhanced_text.replace(
                            entity,
                            f"<{pattern_type}>{entity}</{pattern_type}>"
                        )
            
            # 提取和学习新的关键词
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
            new_keywords = set()
            for word in words:
                if len(word) > 1:  # 忽略单字词
                    self.keywords['general'].add(word)
                    new_keywords.add(word)
                    self.statistics['keywords_learned'] += 1
            
            # 应用上下文增强
            context_info = self._enhance_with_context(enhanced_text, context)
            
            # 评估模式效果
            self._evaluate_pattern_effectiveness(text, general_entities + scene_entities)
            
            result = {
                'text': enhanced_text,
                'scene': scene_info,
                'entities': general_entities + scene_entities,
                'context_enhancements': context_info,
                'new_keywords': list(new_keywords),
                'statistics': {
                    'entities_found': len(general_entities) + len(scene_entities),
                    'context_enhancements': len(context_info),
                    'new_keywords': len(new_keywords)
                }
            }
            
            self.logger.info(f"处理完成: 发现 {result['statistics']['entities_found']} 个实体, "
                           f"{result['statistics']['context_enhancements']} 个上下文增强, "
                           f"{result['statistics']['new_keywords']} 个新关键词")
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理文本时出错: {str(e)}")
            return {'text': text, 'error': str(e)}

    def _detect_scene(self, text: str) -> Dict[str, Any]:
        """检测文本场景"""
        scene_scores = defaultdict(float)
        
        for scene, patterns in self.scene_patterns.items():
            score = 0
            for indicator in patterns['indicators']:
                matches = re.findall(indicator, text)
                score += len(matches) * 0.5
            scene_scores[scene] = score
        
        if scene_scores:
            best_scene = max(scene_scores.items(), key=lambda x: x[1])
            if best_scene[1] > 0:
                return {
                    'scene': best_scene[0],
                    'confidence': min(best_scene[1], 1.0),
                    'all_scores': dict(scene_scores)
                }
        
        return {'scene': None, 'confidence': 0.0, 'all_scores': dict(scene_scores)}

    def _apply_scene_patterns(self, text: str, scene: str) -> List[Dict[str, Any]]:
        """应用场景特定模式"""
        if not scene or scene not in self.scene_patterns:
            return []
            
        entities = []
        patterns = self.scene_patterns[scene]['patterns']
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'type': f"{scene}_{entity_type}",
                    'text': match.group(1),
                    'start': match.start(1),
                    'end': match.end(1)
                })
        
        return entities

    def _enhance_with_context(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """使用上下文信息增强文本"""
        enhancements = []
        try:
            # 分析句子关系
            sentences = re.split(r'[。！？\n]', text)
            
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                
                # 上下文关联分析
                context_info = {
                    'prev': sentences[i-1] if i > 0 else '',
                    'next': sentences[i+1] if i < len(sentences)-1 else '',
                    'external': context or {}
                }
                
                # 寻找关联信息
                for pattern_type, patterns in self.patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, sentence):
                            # 在上下文中查找相关信息
                            for ctx_type, ctx_text in context_info.items():
                                if isinstance(ctx_text, str) and re.search(pattern, ctx_text):
                                    self.statistics['entities_enhanced'] += 1
                                    enhancements.append({
                                        'sentence': sentence,
                                        'context_type': ctx_type,
                                        'pattern_type': pattern_type,
                                        'enhancement': f"Found {pattern_type} context in {ctx_type}"
                                    })
            
            return enhancements
            
        except Exception as e:
            self.logger.error(f"上下文增强失败: {str(e)}")
            return []

    def _evaluate_pattern_effectiveness(self, text: str, entities: List[Dict[str, Any]]):
        """评估模式效果"""
        for pattern_type in self.patterns:
            stats = self.statistics['pattern_effectiveness'][pattern_type]
            stats['total'] += 1
            if any(e['type'] == pattern_type for e in entities):
                stats['matches'] += 1

    def learn_from_feedback(self, text: str, feedback: Dict[str, Any]):
        """从反馈中学习新的模式和规则"""
        try:
            if 'patterns' in feedback:
                for pattern_type, new_patterns in feedback['patterns'].items():
                    self.patterns[pattern_type].extend(new_patterns)
                    self.logger.info(f"学习了新的{pattern_type}模式: {len(new_patterns)}个")
                    
            if 'keywords' in feedback:
                for keyword_type, new_keywords in feedback['keywords'].items():
                    self.keywords[keyword_type].update(new_keywords)
                    self.logger.info(f"学习了新的{keyword_type}关键词: {len(new_keywords)}个")
            
            if 'scene_patterns' in feedback:
                for scene, patterns in feedback['scene_patterns'].items():
                    if scene not in self.scene_patterns:
                        self.scene_patterns[scene] = {'indicators': [], 'patterns': {}}
                    self.scene_patterns[scene]['indicators'].extend(patterns.get('indicators', []))
                    self.scene_patterns[scene]['patterns'].update(patterns.get('patterns', {}))
                    self.logger.info(f"学习了新的场景模式: {scene}")
            
            # 更新统计信息
            self.statistics['patterns_learned'] += len(feedback.get('patterns', {}))
            self.statistics['keywords_learned'] += len(feedback.get('keywords', {}))
            
        except Exception as e:
            self.logger.error(f"从反馈中学习失败: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = dict(self.statistics)
        # 计算模式效果
        pattern_effectiveness = {}
        for pattern_type, data in self.statistics['pattern_effectiveness'].items():
            if data['total'] > 0:
                effectiveness = data['matches'] / data['total']
                pattern_effectiveness[pattern_type] = {
                    'effectiveness': effectiveness,
                    'matches': data['matches'],
                    'total': data['total']
                }
        stats['pattern_effectiveness'] = pattern_effectiveness
        return stats 