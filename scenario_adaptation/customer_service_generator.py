# customer_service_generator.py
from typing import List, Dict
from .schemas import DialogTurn, IntentType, DialogRole  # 移除未使用的Optional
from information_extraction.schemas import ProcessedChunk

class CustomerServiceGenerator:
    def __init__(self, config: Dict):
        self.intent_mapping = config.get("intent_mapping", {
            "CREDIT_CARD": IntentType.CARD_FRAUD,
            "AMOUNT": IntentType.BALANCE_QUERY
        })
        self.response_templates = config.get("response_templates", {
            IntentType.CARD_FRAUD: "已冻结信用卡{card}，可疑交易金额{amount}，时间{date}",
            IntentType.BALANCE_QUERY: "您的账户余额为{amount}"
        })

    def generate_dialog(self, chunk: ProcessedChunk) -> List[DialogTurn]:
        intent = self._detect_intent(chunk)
        user_turn = self._build_user_turn(chunk, intent)
        assistant_turn = self._build_assistant_turn(chunk, intent)
        return [user_turn, assistant_turn]

    def _detect_intent(self, chunk: ProcessedChunk) -> IntentType:
        entity_labels = {e.label for e in chunk.entities}
        for label, intent in self.intent_mapping.items():
            if label in entity_labels:
                return intent
        return IntentType.OTHER

    @staticmethod  # 声明为静态方法
    def _build_user_turn(chunk: ProcessedChunk, intent: IntentType) -> DialogTurn:
        if intent == IntentType.CARD_FRAUD:
            card_entity = next((e for e in chunk.entities if e.label == "CREDIT_CARD"), None)
            content = f"我的信用卡{card_entity.text}有可疑交易" if card_entity else chunk.original_text
        else:
            content = chunk.original_text
        return DialogTurn(role=DialogRole.USER, content=content, intent=intent)  # 使用枚举类型

    def _build_assistant_turn(self, chunk: ProcessedChunk, intent: IntentType) -> DialogTurn:
        template = self.response_templates.get(intent)
        if not template:
            return DialogTurn(role=DialogRole.ASSISTANT, content="已收到您的反馈", intent=intent)
        slots = {
            "card": next((e.text for e in chunk.entities if e.label == "CREDIT_CARD"), "未知卡号"),
            "amount": next((e.text for e in chunk.entities if e.label == "AMOUNT"), "未知金额"),
            "date": next((e.text for e in chunk.entities if e.label == "DATE"), "未知时间")
        }
        return DialogTurn(
            role=DialogRole.ASSISTANT,
            content=template.format(**slots),
            intent=intent
        )