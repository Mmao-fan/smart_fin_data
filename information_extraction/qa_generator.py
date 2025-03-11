#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any, Optional
import re
import logging
import random
from .entity_extractor import FinancialEntityExtractor
from .schemas import Entity

class QAPairGenerator:
    """问答对生成器"""
    
    def __init__(self):
        self.entity_extractor = FinancialEntityExtractor()
        
        # 更自然的问题模板
        self.templates = {
            "customer_service": [
                {"q": "请问{entity}的具体情况是什么？", "a": "根据资料显示，{context}"},
                {"q": "能否介绍一下{entity}的详细信息？", "a": "根据文档记录，{context}"},
                {"q": "关于{entity}，有哪些重要信息需要了解？", "a": "主要信息如下：{context}"}
            ],
            "fraud_detection": [
                {"q": "在{entity}中是否发现了异常情况？", "a": "经分析发现，{context}"},
                {"q": "{entity}的交易记录中有什么值得关注的地方？", "a": "监测到以下异常：{context}"},
                {"q": "从风控角度来看，{entity}是否存在风险？", "a": "风险评估结果显示：{context}"}
            ],
            "compliance": [
                {"q": "{entity}需要遵守哪些合规要求？", "a": "主要合规要求包括：{context}"},
                {"q": "请说明{entity}相关的监管规定。", "a": "相关监管规定如下：{context}"},
                {"q": "{entity}在合规方面有哪些关键点？", "a": "合规关键点包括：{context}"}
            ]
        }
        
        # 上下文连接词
        self.context_connectors = [
            "此外", "同时", "另外", "值得注意的是", "需要说明的是",
            "特别是", "具体来说", "总的来说", "从整体来看"
        ]
        
        self.key_patterns = {
            "金额": r'(?:(?:人民币|美元|欧元|日元|港币)?(?:\d+(?:\.\d+)?(?:万|亿|千|百|十)?元?)|\$\d+(?:\.\d+)?[KMB]?)',
            "日期": r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',
            "时间": r'\d{1,2}:\d{2}(?::\d{2})?',
            "地点": r'[\u4e00-\u9fa5]{2,}(?:省|市|区|县)',
            "机构": r'[\u4e00-\u9fa5]{2,}(?:公司|银行|集团|企业)',
            "人名": r'[\u4e00-\u9fa5]{2,3}(?:先生|女士|总经理|经理)',
            "产品": r'[\u4e00-\u9fa5]{2,}(?:产品|服务|系统|平台)',
            "数字": r'\d+(?:\.\d+)?(?:%|万|亿)?'
        }
        
    def generate_qa_pairs(self, text: str, scenario: str = None, num_pairs: int = 3) -> List[Dict[str, str]]:
        """生成问答对"""
        if not text or not scenario:
            return []
            
        # 提取实体
        entities = self.entity_extractor.extract_entities(text)
        if not entities:
            return []
            
        # 获取场景模板
        templates = self.templates.get(scenario, self.templates["customer_service"])
        
        qa_pairs = []
        used_entities = set()
        
        # 为每个重要实体生成问答对
        for entity in entities:
            if len(qa_pairs) >= num_pairs:
                break
                
            # 避免重复使用相同实体
            if entity.text in used_entities:
                continue
                
            # 获取实体上下文
            context = self._get_entity_context(text, entity)
            if not context:
                continue
                
            # 选择模板
            template = random.choice(templates)
            
            # 生成问答对
            question = template["q"].format(entity=entity.text)
            answer = template["a"].format(context=context)
            
            # 确保答案完整性
            if len(answer) > 10:  # 避免过短的答案
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "entity": entity.text,
                    "entity_type": entity.type
                })
                used_entities.add(entity.text)
        
        return qa_pairs

    def _get_entity_context(self, text: str, entity: Entity, window_size: int = 100) -> Optional[str]:
        """获取实体的上下文"""
        try:
            # 获取实体所在句子
            sentences = re.split(r'[。！？!?]', text)
            entity_sentence = ""
            related_sentences = []
            
            # 找到实体所在句子和相关句子
            for i, sentence in enumerate(sentences):
                if entity.text in sentence:
                    entity_sentence = sentence.strip()
                    # 获取前后句子
                    if i > 0:
                        related_sentences.append(sentences[i-1].strip())
                    if i < len(sentences) - 1:
                        related_sentences.append(sentences[i+1].strip())
                    break
            
            if not entity_sentence:
                return None
                
            # 构建上下文
            context = entity_sentence
            
            # 如果相关句子中包含关联信息，添加到上下文
            for sentence in related_sentences:
                if any(term in sentence for term in self.entity_extractor.financial_terms.get(entity.type, [])):
                    connector = random.choice(self.context_connectors)
                    context += f"，{connector}，{sentence}"
            
            return context
            
        except Exception as e:
            logging.error(f"获取实体上下文失败: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        # 确保标点符号前后格式正确
        text = re.sub(r'\s*([，。！？,.])\s*', r'\1', text)
        # 修复可能的标点符号重复
        text = re.sub(r'([，。！？,.])([，。！？,.])+', r'\1', text)
        return text

    def _split_into_contexts(self, text: str, max_length: int = 200) -> List[str]:
        """将文本分割成上下文窗口"""
        contexts = []
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        
        current_context = ""
        for sentence in sentences:
            if len(current_context) + len(sentence) <= max_length:
                current_context += sentence
            else:
                if current_context:
                    contexts.append(current_context)
                current_context = sentence
                
        if current_context:
            contexts.append(current_context)
            
        return contexts
        
    def _extract_key_entities(self, text: str) -> List[str]:
        """提取关键实体"""
        entities = []
        for entity_type, pattern in self.key_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(match.group())
                
        # 如果没有找到实体，使用关键词
        if not entities:
            keywords = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
            if keywords:
                entities.extend(keywords[:2])
                
        return list(set(entities))
    
    def _generate_entity_based_qa(self, text: str, entities: List[Entity]) -> List[Dict[str, str]]:
        """基于实体生成问答对"""
        qa_pairs = []
        
        # 按实体类型分组
        entity_by_type = {}
        for entity in entities:
            if entity.label not in entity_by_type:
                entity_by_type[entity.label] = []
            entity_by_type[entity.label].append(entity)
        
        # 为每种类型的实体生成问答对
        for entity_type, entity_list in entity_by_type.items():
            if entity_type in self.templates:
                # 选择最多3个该类型的实体
                for entity in entity_list[:3]:
                    # 随机选择一个问题模板
                    template = random.choice(self.templates[entity_type])
                    question = template["q"].format(entity=entity.text)
                    
                    # 生成答案（使用实体上下文）
                    answer = template["a"].format(context=self._generate_answer_for_entity(text, entity))
                    
                    qa_pairs.append({
                        'question': question,
                        'answer': answer
                    })
        
        return qa_pairs
    
    def _generate_general_qa(self, text: str) -> List[Dict[str, str]]:
        """生成通用问答对"""
        qa_pairs = []
        
        # 选择2-3个通用问题
        num_questions = min(len(self.general_templates), random.randint(2, 3))
        selected_templates = random.sample(self.general_templates, num_questions)
        
        for template in selected_templates:
            # 生成答案
            answer = self._generate_general_answer(text, template)
            
            qa_pairs.append({
                'question': template,
                'answer': answer
            })
        
        return qa_pairs
    
    def _generate_scenario_qa(self, text: str, scenario: str) -> List[Dict[str, str]]:
        """生成场景特定问答对"""
        qa_pairs = []
        
        if scenario not in self.scenario_templates:
            return qa_pairs
        
        # 提取关键主题
        topics = self._extract_topics(text)
        
        # 为每个主题生成问答对
        for topic in topics[:2]:  # 最多使用2个主题
            # 随机选择一个问题模板
            template = random.choice(self.scenario_templates[scenario])
            question = template.format(topic=topic)
            
            # 生成答案
            answer = self._generate_scenario_answer(text, topic, scenario)
            
            qa_pairs.append({
                'question': question,
                'answer': answer
            })
        
        return qa_pairs
    
    def _extract_topics(self, text: str) -> List[str]:
        """从文本中提取主题"""
        try:
            # 简单实现：使用实体作为主题
            entities = self.entity_extractor.extract_entities(text)
            
            # 选择特定类型的实体作为主题
            topic_entity_types = ['BANK', 'TRANSACTION_TYPE', 'TERM']
            topics = []
            
            for entity in entities:
                if entity.label in topic_entity_types and entity.text not in topics:
                    topics.append(entity.text)
            
            # 如果没有找到合适的主题，使用一些通用主题
            if not topics:
                topics = ["金融服务", "账户管理", "交易安全", "客户权益"]
            
            return topics
        except Exception as e:
            logging.error(f"提取主题时出错: {str(e)}")
            return ["金融服务", "账户管理"]
    
    def _generate_answer_for_entity(self, text: str, entity: Entity) -> str:
        """为实体生成答案"""
        try:
            # 查找实体所在的上下文
            start_pos = max(0, entity.start - 100)
            end_pos = min(len(text), entity.end + 100)
            context = text[start_pos:end_pos]
            
            # 简单实现：返回包含实体的句子
            sentences = re.split(r'(?<=[。！？.!?])\s+', context)
            for sentence in sentences:
                if entity.text in sentence:
                    return sentence
            
            # 如果没有找到包含实体的句子，返回一个通用答案
            return f"关于{entity.text}的信息，请参考文档中的相关内容。"
        except Exception as e:
            logging.error(f"为实体生成答案时出错: {str(e)}")
            return f"关于{entity.text}的信息，请参考文档中的相关内容。"
    
    def _generate_general_answer(self, text: str, question: str) -> str:
        """生成通用问题的答案"""
        # 简单实现：返回文档的前200个字符作为摘要
        if len(text) > 200:
            return text[:200] + "..."
        return text
    
    def _generate_scenario_answer(self, text: str, topic: str, scenario: str) -> str:
        """生成场景特定问题的答案"""
        try:
            # 查找包含主题的段落
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                if topic in paragraph and len(paragraph) > 50:
                    return paragraph
            
            # 如果没有找到相关段落，返回场景特定的通用答案
            scenario_answers = {
                'customer_service': f"关于{topic}的客户服务问题，我们提供专业的咨询和解决方案。请联系客服热线获取更多帮助。",
                'fraud_detection': f"在{topic}相关的交易中，我们建议您密切关注账户变动，发现异常及时报告。",
                'compliance': f"关于{topic}的合规要求，请参考最新的监管规定和内部政策，确保所有操作符合法规要求。"
            }
            
            return scenario_answers.get(scenario, f"关于{topic}的信息，请参考文档中的相关内容。")
        except Exception as e:
            logging.error(f"生成场景答案时出错: {str(e)}")
            return f"关于{topic}的信息，请参考文档中的相关内容。" 