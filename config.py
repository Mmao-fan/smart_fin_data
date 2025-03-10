# -*- coding: utf-8 -*-
# config.py

# 客服场景配置
CUSTOMER_SERVICE_CONFIG = {
    "intent_mapping": {
        "CREDIT_CARD": "card_issue",
        "ACCOUNT": "account_management",
        "BANK": "bank_info",
        "ACQUISITION": "acquisition_info",
        "TRANSACTION": "transaction_query"
    },
    "response_templates": {
        "card_issue": "您的信用卡{card_number}在{date}的{amount}消费已标记可疑，请确认：<验证链接>",
        "account_management": "账户{account_number}当前余额为：{balance}",
        "bank_info": "花旗银行是一家全球性银行，提供多种金融服务。{bank}在全球多个国家设有分支机构。",
        "acquisition_info": "关于{bank}的收购信息，我们可以提供最新的市场动态和分析。根据最新消息，花旗银行正在考虑新的战略合作伙伴关系。",
        "transaction_query": "您的交易记录已查询，最近一笔交易金额为{amount}，发生在{date}。",
        "other": "感谢您的咨询，我们的客服人员会尽快回复您的问题。"
    }
}

# 欺诈检测配置
FRAUD_DETECTION_CONFIG = {
    "thresholds": {
        "large_amount": 10000,  # 大额交易阈值
        "high_frequency": 3,     # 高频交易次数阈值
        "time_window": 15        # 高频交易时间窗口（分钟）
    },
    "risk_levels": {
        "low": 1,
        "medium": 2,
        "high": 3
    }
}

# 合规映射配置
COMPLIANCE_CONFIG = {
    "regulation_mapping": {
        "KYC": "know_your_customer",
        "AML": "anti_money_laundering",
        "GDPR": "data_protection"
    }
}