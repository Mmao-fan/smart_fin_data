# customer_service_generator.py
from typing import List, Dict
from .schemas import DialogTurn, IntentType, DialogRole
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

    def generate_dialog(self, chunk: ProcessedChunk) -> Dict:  # 修改返回类型为Dict
        """生成对话数据，并保留原始文本"""
        intent = self._detect_intent(chunk)
        user_turn = self._build_user_turn(chunk, intent)
        assistant_turn = self._build_assistant_turn(chunk, intent)
        return {
            "original_text": chunk.original_text,  # 新增字段
            "dialog": [user_turn, assistant_turn],  # 原对话数据
            "intent": intent.value  # 新增意图标签
        }

    # 其他方法保持不变（_detect_intent, _build_user_turn, _build_assistant_turn）