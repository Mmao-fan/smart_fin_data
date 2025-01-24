# config.py
CUSTOMER_SERVICE_CONFIG = {
    "intent_mapping": {
        "CREDIT_CARD": "card_issue",
        "ACCOUNT": "account_management"
    },
    "response_templates": {
        "card_issue": "您的信用卡{card_number}在{date}的{amount}消费已标记可疑，请确认：<验证链接>",
        "account_management": "账户{account_number}当前余额为：{balance}"
    }
}