# -*- coding: utf-8 -*-
# customer_service_generator.py
from typing import Dict, List, Any, Union
import logging
import re

class CustomerServiceGenerator:
    def __init__(self, config: Dict):
        self.intent_mapping = config.get("intent_mapping", {
            "CREDIT_CARD": "card_fraud",
            "AMOUNT": "balance_query",
            "BANK": "bank_info",
            "ACQUISITION": "acquisition_info"
        })
        self.response_templates = config.get("response_templates", {
            "card_fraud": "已冻结信用卡{card}，可疑交易金额{amount}，时间{date}",
            "balance_query": "您的账户余额为{amount}",
            "bank_info": "花旗银行是一家全球性银行，提供多种金融服务。{bank}在全球多个国家设有分支机构。",
            "acquisition_info": "关于{bank}的收购信息，我们可以提供最新的市场动态和分析。",
            "other": "感谢您的咨询，我们的客服人员会尽快回复您的问题。"
        })
        
        # 关键词映射到意图
        self.keyword_to_intent = {
            "花旗": "bank_info",
            "花旗银行": "bank_info",
            "收购": "acquisition_info",
            "并购": "acquisition_info",
            "交易": "card_fraud",
            "信用卡": "card_fraud",
            "余额": "balance_query",
            "账户": "balance_query"
        }

    def generate_dialog(self, chunk) -> Dict:
        """生成客服对话"""
        try:
            # 处理不同类型的输入
            if isinstance(chunk, dict):
                text = chunk.get("text", "")
            elif hasattr(chunk, "original_text"):
                text = getattr(chunk, "original_text", "")
            else:
                text = str(chunk)
                
            # 检测意图
            intent = self._detect_intent(chunk)
            
            # 提取关键信息
            entities = self._extract_entities(text)
            
            return {
                "original_text": text[:200] + "..." if len(text) > 200 else text,  # 截断过长文本
                "dialog": [
                    self._build_user_turn(text, intent, entities),
                    self._build_assistant_turn(text, intent, entities)
                ],
                "intent": intent,
                "entities": entities
            }
        except Exception as e:
            logging.error(f"对话生成失败: {str(e)}", exc_info=True)
            return {
                "original_text": str(chunk)[:100] + "..." if len(str(chunk)) > 100 else str(chunk),
                "dialog": [
                    {"role": "user", "content": "我有一个问题需要咨询", "intent": "other"},
                    {"role": "assistant", "content": "感谢您的咨询，我们的客服人员会尽快回复您的问题。", "intent": "other"}
                ],
                "intent": "other",
                "error": str(e)
            }

    def _detect_intent(self, chunk) -> str:
        """检测意图"""
        # 从实体标签中检测意图
        if hasattr(chunk, "entities"):
            entity_labels = {getattr(e, "label", "") for e in getattr(chunk, "entities", [])}
            for label, intent in self.intent_mapping.items():
                if label in entity_labels:
                    return intent
        
        # 从文本中检测关键词
        text = ""
        if isinstance(chunk, dict):
            text = chunk.get("text", "")
        elif hasattr(chunk, "original_text"):
            text = getattr(chunk, "original_text", "")
        else:
            text = str(chunk)
            
        # 检查关键词
        for keyword, intent in self.keyword_to_intent.items():
            if keyword in text:
                return intent
                
        return "other"

    def _extract_entities(self, text: str) -> Dict[str, str]:
        """从文本中提取实体"""
        entities = {}
        
        # 提取银行名称
        bank_pattern = r"(花旗银行|花旗|汇丰银行|工商银行|建设银行|农业银行)"
        bank_match = re.search(bank_pattern, text)
        if bank_match:
            entities["bank"] = bank_match.group(1)
            
        # 提取金额
        amount_pattern = r"(\d+(?:\.\d+)?)\s*(?:元|美元|USD|CNY|RMB)"
        amount_match = re.search(amount_pattern, text)
        if amount_match:
            entities["amount"] = amount_match.group(1)
            
        # 提取日期
        date_pattern = r"(\d{4}(?:/\d{1,2}){2}|\d{4}年\d{1,2}月\d{1,2}日)"
        date_match = re.search(date_pattern, text)
        if date_match:
            entities["date"] = date_match.group(1)
            
        # 提取信用卡号
        card_pattern = r"(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})"
        card_match = re.search(card_pattern, text)
        if card_match:
            entities["card"] = card_match.group(1)
            
        return entities

    def _build_user_turn(self, text: str, intent: str, entities: Dict[str, str]) -> Dict:
        """构建用户对话轮次"""
        # 根据意图生成用户问题
        if intent == "card_fraud" and "card" in entities:
            content = f"我的信用卡{entities['card']}有可疑交易，请帮我查询"
        elif intent == "balance_query":
            content = "我想查询一下我的账户余额"
        elif intent == "bank_info" and "bank" in entities:
            content = f"请问能告诉我关于{entities['bank']}的信息吗？"
        elif intent == "acquisition_info" and "bank" in entities:
            content = f"我想了解一下关于{entities['bank']}最近的收购新闻"
        else:
            # 从原文中提取第一句话作为用户问题
            sentences = re.split(r'[。！？.!?]', text)
            content = next((s for s in sentences if len(s.strip()) > 5), text[:50])
            
        return {"role": "user", "content": content, "intent": intent}

    def _build_assistant_turn(self, text: str, intent: str, entities: Dict[str, str]) -> Dict:
        """构建助手对话轮次"""
        template = self.response_templates.get(intent, self.response_templates.get("other"))
        
        # 填充模板中的槽位
        try:
            content = template.format(**entities)
        except KeyError:
            # 如果缺少必要的槽位，使用默认回复
            content = self.response_templates.get("other")
            
        return {
            "role": "assistant",
            "content": content,
            "intent": intent
        }