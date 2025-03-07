# customer_service_generator.py
from typing import Dict, List
import logging

class CustomerServiceGenerator:
    def __init__(self, config: Dict):
        self.intent_mapping = config.get("intent_mapping", {
            "CREDIT_CARD": "card_fraud",
            "AMOUNT": "balance_query"
        })
        self.response_templates = config.get("response_templates", {
            "card_fraud": "已冻结信用卡{card}，可疑交易金额{amount}，时间{date}",
            "balance_query": "您的账户余额为{amount}"
        })

    def generate_dialog(self, chunk) -> Dict:
        """保持接口兼容性，优化实体提取逻辑"""
        try:
            intent = self._detect_intent(chunk)
            return {
                "original_text": getattr(chunk, "original_text", ""),
                "dialog": [
                    self._build_user_turn(chunk, intent),
                    self._build_assistant_turn(chunk, intent)
                ],
                "intent": intent
            }
        except Exception as e:
            logging.error(f"对话生成失败: {str(e)}")
            return {}

    def _detect_intent(self, chunk) -> str:
        entity_labels = {getattr(e, "label", "") for e in getattr(chunk, "entities", [])}
        for label, intent in self.intent_mapping.items():
            if label in entity_labels:
                return intent
        return "other"

    def _build_user_turn(self, chunk, intent: str) -> Dict:
        content = getattr(chunk, "original_text", "")
        if intent == "card_fraud":
            card_entity = next((e for e in getattr(chunk, "entities", [])
                              if getattr(e, "label", "") == "CREDIT_CARD"), None)
            if card_entity:
                content = f"我的信用卡{getattr(card_entity, 'text', '')}有可疑交易"
        return {"role": "user", "content": content, "intent": intent}

    def _build_assistant_turn(self, chunk, intent: str) -> Dict:
        template = self.response_templates.get(intent, "已收到您的反馈")
        slots = {
            "card": self._find_entity_text(chunk, "CREDIT_CARD"),
            "amount": self._find_entity_text(chunk, "AMOUNT"),
            "date": self._find_entity_text(chunk, "DATE")
        }
        return {
            "role": "assistant",
            "content": template.format(**slots),
            "intent": intent
        }

    def _find_entity_text(self, chunk, label: str) -> str:
        entities = getattr(chunk, "entities", [])
        return next((getattr(e, "text", "") for e in entities
                    if getattr(e, "label", "") == label), "未知")