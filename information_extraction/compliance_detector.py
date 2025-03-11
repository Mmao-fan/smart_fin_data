# compliance_detector.py
from typing import List, Dict, Any, Optional
import re
import logging
from datetime import datetime
from .schemas import Entity, ComplianceEvent, Relation

class ComplianceDetector:
    """合规事件检测器"""
    
    def __init__(self):
        self.compliance_patterns = {
            "SUSPENSION": {
                "pattern": r"(?:停牌|停止交易|暂停交易)(?:[^。，；]*?(?:原因|事由|说明))?[^。，；]*?[。，；]",
                "importance": "high"
            },
            "DISCLOSURE": {
                "pattern": r"(?:信息披露|公告|披露)[^。，；]*?(?:要求|规定|义务|责任)[^。，；]*?[。，；]",
                "importance": "high"
            },
            "APPROVAL": {
                "pattern": r"(?:审批|批准|核准|同意)[^。，；]*?(?:程序|流程|手续)[^。，；]*?[。，；]",
                "importance": "medium"
            },
            "REGULATION": {
                "pattern": r"(?:监管|合规|规范)[^。，；]*?(?:要求|规定|标准)[^。，；]*?[。，；]",
                "importance": "medium"
            },
            "RISK_CONTROL": {
                "pattern": r"(?:风险控制|内控|合规管理)[^。，；]*?(?:措施|制度|流程)[^。，；]*?[。，；]",
                "importance": "medium"
            },
            "VIOLATION": {
                "pattern": r"(?:违规|违法|违反)[^。，；]*?(?:处罚|惩罚|制裁|罚款)[^。，；]*?[。，；]",
                "importance": "high"
            },
            "MONEY_LAUNDERING": {
                "pattern": r"(?:洗钱|资金|可疑交易)[^。，；]*?(?:监控|报告|调查)[^。，；]*?[。，；]",
                "importance": "high"
            },
            "INSIDER_TRADING": {
                "pattern": r"(?:内幕|内部信息|未公开信息)[^。，；]*?(?:交易|买卖|操作)[^。，；]*?[。，；]",
                "importance": "high"
            },
            "FRAUD": {
                "pattern": r"(?:欺诈|造假|虚假)[^。，；]*?(?:报表|记录|账目)[^。，；]*?[。，；]",
                "importance": "high"
            }
        }
        
        # 价格异常模式
        self.price_patterns = {
            "LOW_PRICE": r"(?:低于|远低于|显著低于)[^。，；]*?(?:市场价|评估价|公允价值)[^。，；]*?[。，；]",
            "HIGH_PRICE": r"(?:高于|远高于|显著高于)[^。，；]*?(?:市场价|评估价|公允价值)[^。，；]*?[。，；]",
            "PRICE_FLUCTUATION": r"(?:价格|股价)(?:波动|变化|变动)(?:异常|剧烈|显著)[^。，；]*?[。，；]"
        }
        
        # 控制权相关模式
        self.control_patterns = {
            "CONTROL_CHANGE": r"(?:控制权|控股权)(?:变更|转让|变化)[^。，；]*?[。，；]",
            "SHAREHOLDER_CHANGE": r"(?:股东|持股比例)(?:变更|变化|调整)[^。，；]*?[。，；]",
            "MANAGEMENT_CHANGE": r"(?:管理层|董事会|高管)(?:变更|调整|改选)[^。，；]*?[。，；]"
        }

    def detect_events(self, text: str, entities: List[Entity], relations: List[Relation]) -> List[ComplianceEvent]:
        """检测合规事件"""
        return self.detect_compliance_events(text)

    def detect_compliance_events(self, text: str) -> List[ComplianceEvent]:
        """检测合规事件"""
        events = []
        
        for event_type, config in self.compliance_patterns.items():
            pattern = config["pattern"]
            importance = config["importance"]
            
            # 设置重要性分数
            if importance == "high":
                importance_score = 0.9
            elif importance == "medium":
                importance_score = 0.6
            else:
                importance_score = 0.3
            
            # 查找匹配
            matches = re.finditer(pattern, text)
            for match in matches:
                event_text = match.group(0)
                
                # 创建合规事件
                event = ComplianceEvent(
                    type=event_type,
                    text=event_text,
                    importance=importance_score,
                    timestamp=datetime.now()
                )
                events.append(event)
        
        return events

    def analyze_compliance_risk(self, events: List[ComplianceEvent]) -> Dict[str, Any]:
        """分析合规风险"""
        if not events:
            return {
                "risk_level": "low",
                "risk_score": 0.1,
                "summary": "未检测到明显合规风险",
                "recommendations": ["保持常规合规监控"]
            }
        
        # 计算风险分数
        risk_score = sum(event.importance for event in events) / len(events)
        
        # 确定风险等级
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # 生成风险摘要
        event_types = set(event.type for event in events)
        summary = f"检测到 {len(events)} 个合规事件，涉及 {len(event_types)} 种类型。"
        
        # 生成建议
        recommendations = []
        if "VIOLATION" in event_types or "FRAUD" in event_types:
            recommendations.append("立即进行合规审查，并考虑向监管机构报告")
        if "MONEY_LAUNDERING" in event_types:
            recommendations.append("加强反洗钱监控，审查可疑交易")
        if "INSIDER_TRADING" in event_types:
            recommendations.append("审查内幕交易防控措施，加强信息隔离墙建设")
        if "DISCLOSURE" in event_types:
            recommendations.append("确保信息披露及时、准确、完整")
        
        # 如果没有特定建议，添加通用建议
        if not recommendations:
            recommendations.append("加强合规培训和内部控制")
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "summary": summary,
            "recommendations": recommendations
        } 