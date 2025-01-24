# customer_service_generator.py
from typing import List, Dict
from .schemas import DialogTurn
from information_extraction.schemas import ProcessedChunk

class CustomerServiceGenerator:
    def __init__(self, config: Dict):
        self.intent_mapping = config.get("intent_mapping", {})
        self.response_templates = config.get("response_templates", {})

    def generate_dialog(self, chunk: ProcessedChunk) -> List[DialogTurn]:
        """生成客户服务对话数据"""
        intent = self._detect_intent(chunk)
        user_turn = self._build_user_turn(chunk, intent)
        assistant_turn = self._build_assistant_turn(chunk, intent)
        return [user_turn, assistant_turn]

    def _detect_intent(self, chunk: ProcessedChunk) -> str:
        """基于实体类型检测用户意图"""
        entity_labels = {e.label for e in chunk.entities}
        for label, intent in self.intent_mapping.items():
            if label in entity_labels:
                return intent
        return "other"

    def _build_user_turn(self, chunk: ProcessedChunk, intent: str) -> DialogTurn:
        """构建用户提问轮次"""
        if intent == "card_fraud":
            card_entity = next(e for e in chunk.entities if e.label == "CREDIT_CARD")
            return DialogTurn(
                role="user",
                content=f"我的信用卡{card_entity.text}有可疑交易",
                intent=intent
            )
        return DialogTurn(
            role="user",
            content=chunk.original_text,
            intent=intent
        )

    def _build_assistant_turn(self, chunk: ProcessedChunk, intent: str) -> DialogTurn:
        """构建客服回答轮次"""
        template = self.response_templates.get(intent)
        if template:
            return DialogTurn(
                role="assistant",
                content=template.format(**self._extract_slots(chunk)),
                intent=intent
            )
        return DialogTurn(
            role="assistant",
            content="已收到您的反馈，我们将尽快处理",
            intent=intent
        )

    def _extract_slots(self, chunk: ProcessedChunk) -> Dict:
        """提取模板填充槽位"""
        slots = {}
        for e in chunk.entities:
            if e.label == "DATE":
                slots["date"] = e.text
            elif e.label == "AMOUNT":
                slots["amount"] = e.text
        return slots