# formatter.py
import json
from typing import List, Dict, Optional, Any
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
import uuid

class DataFormatter:
    def __init__(self):
        self.scene_formatters = {
            'CUSTOMER_SERVICE': self._format_customer_service_data,
            'FRAUD_DETECTION': self._format_fraud_detection_data,
            'COMPLIANCE': self._format_compliance_data
        }
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)

    def format_data(self, data: Dict[str, Any], scenario_type: str) -> Dict[str, Any]:
        """根据不同场景格式化数据
        
        Args:
            data: 原始数据
            scenario_type: 场景类型
            
        Returns:
            格式化后的数据
        """
        self.logger.info(f"格式化数据，场景类型: {scenario_type}")
        
        # 检查数据有效性
        if not data:
            self.logger.warning("输入数据为空")
            return {}
            
        # 添加超时保护
        start_time = datetime.now()
        max_processing_time = 10  # 最大处理时间10秒
        
        # 提取基本信息
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        anomalies = data.get("anomalies", [])
        metadata = data.get("metadata", {})
        text = data.get("text", "")
        
        # 限制实体和关系的数量，防止处理过多数据
        max_entities = 100
        max_relations = 100
        
        if len(entities) > max_entities:
            self.logger.warning(f"实体数量过多 ({len(entities)}), 限制为 {max_entities}")
            entities = entities[:max_entities]
            
        if len(relations) > max_relations:
            self.logger.warning(f"关系数量过多 ({len(relations)}), 限制为 {max_relations}")
            relations = relations[:max_relations]
        
        # 确保实体和关系是字典格式
        if entities and isinstance(entities[0], dict):
            # 已经是字典格式，不需要转换
            pass
        else:
            # 需要转换为字典格式
            self.logger.info("将实体转换为字典格式")
            entities = self._convert_entities_to_dicts(entities)
            
        if relations and isinstance(relations[0], dict):
            # 已经是字典格式，不需要转换
            pass
        else:
            # 需要转换为字典格式
            self.logger.info("将关系转换为字典格式")
            relations = self._convert_relations_to_dicts(relations)
        
        # 记录实体和关系数量
        self.logger.info(f"实体数量: {len(entities)}, 关系数量: {len(relations)}, 异常数量: {len(anomalies)}")
        
        # 检查处理时间
        elapsed_time = (datetime.now() - start_time).total_seconds()
        if elapsed_time > max_processing_time:
            self.logger.warning(f"数据格式化超时 ({elapsed_time:.2f}秒)，返回简化结果")
            return {
                "input": {"text": text[:500] if text else ""},
                "output": {"message": "处理超时"},
                "metadata": {"scenario": scenario_type, "timeout": True}
            }
        
        # 根据场景类型选择不同的格式化方法
        try:
            formatted_data = None
            if scenario_type.lower() == "customer_service":
                formatted_data = self._format_customer_service_data(entities, relations, anomalies, text, metadata)
            elif scenario_type.lower() == "fraud_detection":
                formatted_data = self._format_fraud_detection_data(entities, relations, anomalies, text, metadata)
            elif scenario_type.lower() == "compliance":
                formatted_data = self._format_compliance_data(entities, relations, anomalies, text, metadata)
            else:
                formatted_data = self._format_general_data(entities, relations, anomalies, text, metadata)
            
            # 保存训练数据
            self._save_training_data(formatted_data, scenario_type)
            
            return formatted_data
        except Exception as e:
            self.logger.error(f"格式化数据时出错: {str(e)}")
            # 返回简化结果
            return {
                "input": {"text": text[:500] if text else ""},
                "output": {"error": str(e)},
                "metadata": {"scenario": scenario_type, "error": True}
            }
            
    def _format_customer_service_data(self, entities: List[Dict], relations: List[Dict], 
                                     anomalies: List[Dict], text: str, metadata: Dict) -> Dict[str, Any]:
        """格式化客户服务场景数据
        
        Args:
            entities: 实体列表
            relations: 关系列表
            anomalies: 异常列表
            text: 原始文本
            metadata: 元数据
            
        Returns:
            格式化后的数据
        """
        # 提取客户相关实体
        customer_entities = self._extract_customer_entities(entities)
        
        # 提取产品相关实体
        product_entities = self._extract_product_entities(entities)
        
        # 提取问题相关实体
        issue_entities = self._extract_issue_entities(entities)
        
        # 生成问题
        question = self._generate_customer_question(customer_entities, product_entities, issue_entities)
        
        # 生成回答
        answer = self._generate_customer_service_answer(customer_entities, product_entities, issue_entities, relations)
        
        # 构建输出数据
        formatted_data = {
            "input": {
                "text": text[:500] if text else "",  # 限制文本长度
                "entities": self._filter_and_format_entities(entities, ["PERSON", "PRODUCT", "ISSUE", "DATE", "ORGANIZATION"]),
                "customer_info": customer_entities
            },
            "output": {
                "question": question,
                "answer": answer
            },
            "metadata": {
                "source": metadata.get("source", "unknown"),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "confidence": metadata.get("confidence", 0.8),
                "scenario": "customer_service"
            }
        }

        return formatted_data

    def _format_fraud_detection_data(self, entities: List[Dict], relations: List[Dict], 
                                    anomalies: List[Dict], text: str, metadata: Dict) -> Dict[str, Any]:
        """格式化欺诈检测场景数据
        
        Args:
            entities: 实体列表
            relations: 关系列表
            anomalies: 异常列表
            text: 原始文本
            metadata: 元数据
            
        Returns:
            格式化后的数据
        """
        # 提取交易相关实体
        transaction_entities = self._extract_transaction_entities(entities)
        
        # 提取账户相关实体
        account_entities = self._extract_account_entities(entities)
        
        # 提取风险相关实体
        risk_entities = self._extract_risk_entities(entities, anomalies)
        
        # 评估风险等级
        risk_level = self._assess_risk_level(risk_entities, anomalies)
        
        # 生成风险报告
        risk_report = self._generate_risk_report(transaction_entities, account_entities, risk_entities, risk_level)

        # 生成建议
        recommendations = self._generate_fraud_recommendations(risk_level, risk_entities, anomalies)

        # 构建输出数据
        formatted_data = {
            "input": {
                "transaction_data": text[:500] if text else "",  # 限制文本长度
                "entities": self._filter_and_format_entities(entities, ["MONEY", "DATE", "PERSON", "ORGANIZATION", "ACCOUNT", "TRANSACTION"]),
                "transaction_info": transaction_entities,
                "account_info": account_entities
            },
            "output": {
                "risk_report": {
                    "risk_level": risk_level,
                    "risk_factors": risk_entities,
                    "recommendations": recommendations
                }
            },
            "metadata": {
                "source": metadata.get("source", "unknown"),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "confidence": metadata.get("confidence", 0.8),
                "scenario": "fraud_detection"
            }
        }

        return formatted_data

    def _format_compliance_data(self, entities: List[Dict], relations: List[Dict], 
                               anomalies: List[Dict], text: str, metadata: Dict) -> Dict[str, Any]:
        """格式化合规场景数据
        
        Args:
            entities: 实体列表
            relations: 关系列表
            anomalies: 异常列表
            text: 原始文本
            metadata: 元数据
            
        Returns:
            格式化后的数据
        """
        # 提取业务相关实体
        business_entities = self._extract_business_entities(entities)
        
        # 提取法规相关实体
        regulation_entities = self._extract_regulation_entities(entities)
        
        # 提取风险相关实体
        risk_entities = self._extract_risk_entities(entities, anomalies)

        # 评估合规状态
        compliance_status = self._assess_compliance_status(business_entities, regulation_entities, risk_entities, anomalies)

        # 生成建议
        recommendations = self._generate_compliance_recommendations(compliance_status, business_entities, regulation_entities, risk_entities)
        
        # 构建输出数据
        formatted_data = {
            "input": {
                "document_text": text[:500] if text else "",  # 限制文本长度
                "entities": self._filter_and_format_entities(entities, ["ORGANIZATION", "REGULATION", "DATE", "PERSON", "MONEY"]),
                "business_info": business_entities,
                "regulation_info": regulation_entities
            },
            "output": {
                "compliance_report": {
                    "status": compliance_status,
                    "risk_factors": risk_entities,
                    "recommendations": recommendations
                }
            },
            "metadata": {
                "source": metadata.get("source", "unknown"),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "confidence": metadata.get("confidence", 0.8),
                "scenario": "compliance"
            }
        }

        return formatted_data

    def _format_general_data(self, entities: List[Dict], relations: List[Dict], 
                            anomalies: List[Dict], text: str, metadata: Dict) -> Dict[str, Any]:
        """格式化通用场景数据
        
        Args:
            entities: 实体列表
            relations: 关系列表
            anomalies: 异常列表
            text: 原始文本
            metadata: 元数据
            
        Returns:
            格式化后的数据
        """
        # 生成摘要
        summary = self._generate_summary(entities, relations, text)
        
        # 构建输出数据
        formatted_data = {
            "input": {
                "text": text[:500] if text else "",  # 限制文本长度
            },
            "output": {
                "entities": self._filter_and_format_entities(entities),
                "relations": self._filter_and_format_relations(relations),
                "anomalies": anomalies,
                "summary": summary
            },
            "metadata": {
                "source": metadata.get("source", "unknown"),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "confidence": metadata.get("confidence", 0.8),
                "scenario": "general"
            }
        }

        return formatted_data

    def _filter_and_format_entities(self, entities: List, entity_types: List[str] = None) -> List[Dict]:
        """过滤和格式化实体
        
        Args:
            entities: 实体列表
            entity_types: 实体类型列表，如果为None则不过滤
            
        Returns:
            过滤和格式化后的实体列表
        """
        if not entities:
            return []
            
        formatted_entities = []
        
        for entity in entities:
            # 检查实体是否为字典或Entity对象
            if isinstance(entity, dict):
                entity_type = entity.get("type", "")
                
                # 如果指定了实体类型，则过滤
                if entity_types and entity_type not in entity_types:
                    continue
                    
                # 格式化实体
                formatted_entity = {
                    "text": entity.get("text", ""),
                    "type": entity_type,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0),
                    "confidence": entity.get("confidence", 0.0)
                }
            else:
                # 假设是Entity对象
                try:
                    entity_type = entity.type if hasattr(entity, 'type') else ""
                    
                    # 如果指定了实体类型，则过滤
                    if entity_types and entity_type not in entity_types:
                        continue
                        
                    # 格式化实体
                    formatted_entity = {
                        "text": entity.text if hasattr(entity, 'text') else "",
                        "type": entity_type,
                        "start": entity.start if hasattr(entity, 'start') else 0,
                        "end": entity.end if hasattr(entity, 'end') else 0,
                        "confidence": entity.confidence if hasattr(entity, 'confidence') else 0.0
                    }
                except AttributeError:
                    # 如果无法访问属性，则跳过
                    self.logger.warning(f"无法处理实体: {entity}")
                    continue
            
            formatted_entities.append(formatted_entity)
            
        return formatted_entities
        
    def _filter_and_format_relations(self, relations: List) -> List[Dict]:
        """过滤和格式化关系
        
        Args:
            relations: 关系列表
            
        Returns:
            过滤和格式化后的关系列表
        """
        if not relations:
            return []
            
        formatted_relations = []
        
        for relation in relations:
            # 检查关系是否为字典或Relation对象
            if isinstance(relation, dict):
                # 格式化关系
                formatted_relation = {
                    "source": relation.get("source", {}).get("text", ""),
                    "target": relation.get("target", {}).get("text", ""),
                    "type": relation.get("type", "UNKNOWN"),
                    "confidence": relation.get("confidence", 0.0)
                }
            else:
                # 假设是Relation对象
                try:
                    # 格式化关系
                    source_text = relation.source.text if hasattr(relation, 'source') and hasattr(relation.source, 'text') else ""
                    target_text = relation.target.text if hasattr(relation, 'target') and hasattr(relation.target, 'text') else ""
                    
                    formatted_relation = {
                        "source": source_text,
                        "target": target_text,
                        "type": relation.type if hasattr(relation, 'type') else "UNKNOWN",
                        "confidence": relation.confidence if hasattr(relation, 'confidence') else 0.0
                    }
                except AttributeError:
                    # 如果无法访问属性，则跳过
                    self.logger.warning(f"无法处理关系: {relation}")
                    continue
            
            formatted_relations.append(formatted_relation)
            
        return formatted_relations
        
    def _extract_customer_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取客户相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            客户相关实体列表
        """
        customer_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["PERSON", "CUSTOMER", "CONTACT", "EMAIL", "PHONE"]:
                customer_entities.append(entity)
                
        return customer_entities
        
    def _extract_product_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取产品相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            产品相关实体列表
        """
        product_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["PRODUCT", "SERVICE", "ITEM"]:
                product_entities.append(entity)
                
        return product_entities
        
    def _extract_issue_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取问题相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            问题相关实体列表
        """
        issue_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["ISSUE", "PROBLEM", "ERROR", "BUG"]:
                issue_entities.append(entity)
                
        return issue_entities
        
    def _generate_customer_question(self, customer_entities: List[Dict], 
                                   product_entities: List[Dict], 
                                   issue_entities: List[Dict]) -> str:
        """生成客户问题
        
        Args:
            customer_entities: 客户相关实体列表
            product_entities: 产品相关实体列表
            issue_entities: 问题相关实体列表
            
        Returns:
            生成的客户问题
        """
        # 如果没有足够的实体信息，返回默认问题
        if not product_entities and not issue_entities:
            return "请问有什么可以帮助您？"
            
        # 构建问题
        question = ""
        
        # 添加产品信息
        if product_entities:
            product = product_entities[0].get("text", "您的产品")
            question += f"关于{product}，"
            
        # 添加问题信息
        if issue_entities:
            issue = issue_entities[0].get("text", "遇到了一些问题")
            question += f"我{issue}，"
            
        # 完成问题
        question += "能帮我解决吗？"
        
        return question
        
    def _generate_customer_service_answer(self, customer_entities: List[Dict], 
                                         product_entities: List[Dict], 
                                         issue_entities: List[Dict],
                                         relations: List[Dict]) -> str:
        """生成客服回答
        
        Args:
            customer_entities: 客户相关实体列表
            product_entities: 产品相关实体列表
            issue_entities: 问题相关实体列表
            relations: 关系列表
            
        Returns:
            生成的客服回答
        """
        # 如果没有足够的实体信息，返回默认回答
        if not product_entities and not issue_entities:
            return "很抱歉，我无法回答您的问题。请提供更多信息，以便我能更好地帮助您。"
            
        # 构建回答
        answer = "感谢您的咨询。"
        
        # 添加客户称呼
        if customer_entities:
            customer = customer_entities[0].get("text", "")
            if customer:
                answer += f"{customer}，"
            
        # 添加产品信息
        if product_entities:
            product = product_entities[0].get("text", "您提到的产品")
            answer += f"关于{product}，"
            
        # 添加问题解决方案
        if issue_entities:
            issue = issue_entities[0].get("text", "您遇到的问题")
            answer += f"针对{issue}，我们建议您尝试以下解决方案：\n"
            answer += "1. 重启设备并重新尝试\n"
            answer += "2. 检查网络连接是否正常\n"
            answer += "3. 更新到最新版本\n"
            
        # 添加结束语
        answer += "\n如果问题仍然存在，请联系我们的技术支持团队。"
        
        return answer
        
    def _extract_transaction_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取交易相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            交易相关实体列表
        """
        transaction_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["TRANSACTION", "MONEY", "DATE", "TIME", "ACCOUNT", "PAYMENT"]:
                transaction_entities.append(entity)
                
        return transaction_entities
        
    def _extract_account_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取账户相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            账户相关实体列表
        """
        account_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["ACCOUNT", "CARD", "BANK", "PERSON", "ORGANIZATION"]:
                account_entities.append(entity)
                
        return account_entities
        
    def _extract_risk_entities(self, entities: List[Dict], anomalies: List[Dict]) -> List[Dict]:
        """提取风险相关实体
        
        Args:
            entities: 实体列表
            anomalies: 异常列表
            
        Returns:
            风险相关实体列表
        """
        risk_entities = []
        
        # 从实体中提取风险相关实体
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["RISK", "FRAUD", "SUSPICIOUS", "UNUSUAL"]:
                risk_entities.append(entity)
                
        # 从异常中提取风险相关实体
        for anomaly in anomalies:
            risk_entities.append({
                "text": anomaly.get("description", "异常交易"),
                "type": "RISK",
                "confidence": anomaly.get("confidence", 0.8)
            })
                
        return risk_entities
        
    def _assess_risk_level(self, risk_entities: List[Dict], anomalies: List[Dict]) -> str:
        """评估风险等级
        
        Args:
            risk_entities: 风险相关实体列表
            anomalies: 异常列表
            
        Returns:
            风险等级
        """
        # 如果没有风险实体和异常，返回低风险
        if not risk_entities and not anomalies:
            return "low"
            
        # 计算风险分数
        risk_score = 0
        
        # 根据风险实体数量增加风险分数
        risk_score += len(risk_entities) * 2
        
        # 根据异常数量增加风险分数
        risk_score += len(anomalies) * 3
        
        # 根据风险分数确定风险等级
        if risk_score >= 10:
            return "high"
        elif risk_score >= 5:
            return "medium"
        else:
            return "low"
            
    def _generate_risk_report(self, transaction_entities: List[Dict], 
                             account_entities: List[Dict], 
                             risk_entities: List[Dict],
                             risk_level: str) -> Dict[str, Any]:
        """生成风险报告
        
        Args:
            transaction_entities: 交易相关实体列表
            account_entities: 账户相关实体列表
            risk_entities: 风险相关实体列表
            risk_level: 风险等级
            
        Returns:
            风险报告
        """
        # 构建风险报告
        risk_report = {
            "risk_level": risk_level,
            "risk_factors": [],
            "transaction_details": {},
            "account_details": {},
            "recommendations": []
        }
        
        # 添加风险因素
        for entity in risk_entities:
            risk_report["risk_factors"].append(entity.get("text", ""))
            
        # 添加交易详情
        for entity in transaction_entities:
            entity_type = entity.get("type", "")
            entity_text = entity.get("text", "")
            
            if entity_type == "MONEY":
                risk_report["transaction_details"]["amount"] = entity_text
            elif entity_type == "DATE":
                risk_report["transaction_details"]["date"] = entity_text
            elif entity_type == "TIME":
                risk_report["transaction_details"]["time"] = entity_text
            elif entity_type == "ACCOUNT":
                risk_report["transaction_details"]["account"] = entity_text
                
        # 添加账户详情
        for entity in account_entities:
            entity_type = entity.get("type", "")
            entity_text = entity.get("text", "")
            
            if entity_type == "ACCOUNT":
                risk_report["account_details"]["account_number"] = entity_text
            elif entity_type == "CARD":
                risk_report["account_details"]["card_number"] = entity_text
            elif entity_type == "BANK":
                risk_report["account_details"]["bank"] = entity_text
            elif entity_type == "PERSON":
                risk_report["account_details"]["account_holder"] = entity_text
                
        # 添加建议
        risk_report["recommendations"] = self._generate_fraud_recommendations(risk_level, risk_entities, [])
        
        return risk_report
        
    def _generate_fraud_recommendations(self, risk_level: str, 
                                       risk_entities: List[Dict], 
                                       anomalies: List[Dict]) -> List[str]:
        """生成欺诈检测建议
        
        Args:
            risk_level: 风险等级
            risk_entities: 风险相关实体列表
            anomalies: 异常列表
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 根据风险等级生成建议
        if risk_level == "high":
            recommendations.append("立即冻结账户并联系客户确认交易")
            recommendations.append("向反欺诈部门报告此交易")
            recommendations.append("对账户进行全面审查")
        elif risk_level == "medium":
            recommendations.append("联系客户确认交易")
            recommendations.append("暂时限制大额交易")
            recommendations.append("监控账户活动24小时")
        else:
            recommendations.append("正常处理交易")
            recommendations.append("定期监控账户活动")
        
        return recommendations

    def _extract_business_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取业务相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            业务相关实体列表
        """
        business_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["ORGANIZATION", "COMPANY", "BUSINESS", "INDUSTRY"]:
                business_entities.append(entity)
                
        return business_entities
        
    def _extract_regulation_entities(self, entities: List[Dict]) -> List[Dict]:
        """提取法规相关实体
        
        Args:
            entities: 实体列表
            
        Returns:
            法规相关实体列表
        """
        regulation_entities = []
        
        for entity in entities:
            entity_type = entity.get("type", "")
            
            if entity_type in ["REGULATION", "LAW", "POLICY", "RULE"]:
                regulation_entities.append(entity)
                
        return regulation_entities
        
    def _assess_compliance_status(self, business_entities: List[Dict], 
                                 regulation_entities: List[Dict], 
                                 risk_entities: List[Dict],
                                 anomalies: List[Dict]) -> str:
        """评估合规状态
        
        Args:
            business_entities: 业务相关实体列表
            regulation_entities: 法规相关实体列表
            risk_entities: 风险相关实体列表
            anomalies: 异常列表
            
        Returns:
            合规状态
        """
        # 如果没有风险实体和异常，返回合规
        if not risk_entities and not anomalies:
            return "compliance"
            
        # 计算风险分数
        risk_score = 0
        
        # 根据风险实体数量增加风险分数
        risk_score += len(risk_entities) * 2
        
        # 根据异常数量增加风险分数
        risk_score += len(anomalies) * 3
        
        # 根据风险分数确定合规状态
        if risk_score >= 5:
            return "non_compliance"
        else:
            return "compliance"
            
    def _generate_compliance_recommendations(self, compliance_status: str, 
                                           business_entities: List[Dict], 
                                           regulation_entities: List[Dict],
                                           risk_entities: List[Dict]) -> List[str]:
        """生成合规建议
        
        Args:
            compliance_status: 合规状态
            business_entities: 业务相关实体列表
            regulation_entities: 法规相关实体列表
            risk_entities: 风险相关实体列表
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 根据合规状态生成建议
        if compliance_status == "non_compliance":
            recommendations.append("立即停止相关业务活动")
            recommendations.append("联系法务部门进行合规审查")
            recommendations.append("制定合规整改计划")
        else:
            recommendations.append("定期进行合规检查")
            recommendations.append("更新合规政策和流程")
            recommendations.append("对员工进行合规培训")
        
        return recommendations

    def _generate_summary(self, entities: List[Dict], relations: List[Dict], text: str) -> str:
        """生成摘要
        
        Args:
            entities: 实体列表
            relations: 关系列表
            text: 原始文本
            
        Returns:
            生成的摘要
        """
        # 如果没有足够的实体和关系，返回默认摘要
        if not entities and not relations:
            return "无法生成摘要，信息不足。"
            
        # 构建摘要
        summary = "文档摘要：\n"
        
        # 添加实体信息
        if entities:
            entity_types = defaultdict(list)
            
            # 按类型分组实体
            for entity in entities:
                entity_type = entity.get("type", "UNKNOWN")
                entity_text = entity.get("text", "")
                
                if entity_text:
                    entity_types[entity_type].append(entity_text)
                    
            # 添加实体信息到摘要
            for entity_type, entity_texts in entity_types.items():
                if entity_texts:
                    summary += f"\n{entity_type}：{', '.join(entity_texts[:5])}"
                    
                    # 如果实体数量超过5个，添加省略号
                    if len(entity_texts) > 5:
                        summary += "等"
                        
        # 添加关系信息
        if relations:
            summary += "\n\n主要关系："
            
            # 最多添加5个关系
            for i, relation in enumerate(relations[:5]):
                source = relation.get("source", {}).get("text", "")
                target = relation.get("target", {}).get("text", "")
                rel_type = relation.get("type", "")
                
                if source and target and rel_type:
                    summary += f"\n- {source} {rel_type} {target}"
                    
        return summary

    def _convert_entities_to_dicts(self, entities: List) -> List[Dict]:
        """将实体对象转换为字典格式
        
        Args:
            entities: 实体列表
            
        Returns:
            字典格式的实体列表
        """
        entity_dicts = []
        
        if not entities:
            return entity_dicts
            
        for entity in entities:
            try:
                if isinstance(entity, dict):
                    # 确保字典包含所有必要的字段
                    entity_dict = {
                        'id': entity.get('id', str(uuid.uuid4())),
                        'text': entity.get('text', ''),
                        'type': entity.get('type', ''),
                        'start': entity.get('start', 0),
                        'end': entity.get('end', 0),
                        'confidence': entity.get('confidence', 0.0),
                        'metadata': entity.get('metadata', {})
                    }
                    entity_dicts.append(entity_dict)
                else:
                    # 假设是Entity对象
                    if hasattr(entity, 'to_dict') and callable(getattr(entity, 'to_dict')):
                        # 使用对象的to_dict方法
                        entity_dict = entity.to_dict()
                    else:
                        # 手动构建字典
                        entity_dict = {
                            'id': getattr(entity, 'id', str(uuid.uuid4())),
                            'text': getattr(entity, 'text', ''),
                            'type': getattr(entity, 'type', ''),
                            'start': getattr(entity, 'start', 0),
                            'end': getattr(entity, 'end', 0),
                            'confidence': getattr(entity, 'confidence', 0.0),
                            'metadata': getattr(entity, 'metadata', {})
                        }
                    entity_dicts.append(entity_dict)
            except Exception as e:
                self.logger.warning(f"转换实体对象时出错: {str(e)}")
                # 尝试创建一个最小的有效实体字典
                try:
                    if hasattr(entity, 'text') or (isinstance(entity, dict) and 'text' in entity):
                        text = getattr(entity, 'text', '') if hasattr(entity, 'text') else entity.get('text', '')
                        entity_type = getattr(entity, 'type', '') if hasattr(entity, 'type') else entity.get('type', '')
                        entity_dict = {
                            'id': str(uuid.uuid4()),
                            'text': text,
                            'type': entity_type,
                            'start': 0,
                            'end': len(text),
                            'confidence': 0.5,
                            'metadata': {}
                        }
                        entity_dicts.append(entity_dict)
                except:
                    pass
                    
        return entity_dicts
        
    def _convert_relations_to_dicts(self, relations: List) -> List[Dict]:
        """将关系对象转换为字典格式
        
        Args:
            relations: 关系列表
            
        Returns:
            字典格式的关系列表
        """
        relation_dicts = []
        
        if not relations:
            return relation_dicts
            
        for relation in relations:
            try:
                if isinstance(relation, dict):
                    # 确保字典包含所有必要的字段
                    source = relation.get('source', {})
                    target = relation.get('target', {})
                    
                    # 处理source和target可能是实体对象的情况
                    if not isinstance(source, dict) and hasattr(source, 'to_dict'):
                        source = source.to_dict()
                    elif not isinstance(source, dict):
                        source = {'text': str(source)}
                        
                    if not isinstance(target, dict) and hasattr(target, 'to_dict'):
                        target = target.to_dict()
                    elif not isinstance(target, dict):
                        target = {'text': str(target)}
                    
                    relation_dict = {
                        'id': relation.get('id', str(uuid.uuid4())),
                        'type': relation.get('type', ''),
                        'source': source,
                        'target': target,
                        'confidence': relation.get('confidence', 0.0),
                        'metadata': relation.get('metadata', {})
                    }
                    relation_dicts.append(relation_dict)
                else:
                    # 假设是Relation对象
                    if hasattr(relation, 'to_dict') and callable(getattr(relation, 'to_dict')):
                        # 使用对象的to_dict方法
                        relation_dict = relation.to_dict()
                    else:
                        # 手动构建字典
                        source = getattr(relation, 'source', None)
                        target = getattr(relation, 'target', None)
                        
                        # 处理source和target可能是实体对象的情况
                        if hasattr(source, 'to_dict'):
                            source = source.to_dict()
                        elif not isinstance(source, dict):
                            source = {'text': str(source)}
                            
                        if hasattr(target, 'to_dict'):
                            target = target.to_dict()
                        elif not isinstance(target, dict):
                            target = {'text': str(target)}
                        
                        relation_dict = {
                            'id': getattr(relation, 'id', str(uuid.uuid4())),
                            'type': getattr(relation, 'type', ''),
                            'source': source,
                            'target': target,
                            'confidence': getattr(relation, 'confidence', 0.0),
                            'metadata': getattr(relation, 'metadata', {})
                        }
                    relation_dicts.append(relation_dict)
            except Exception as e:
                self.logger.warning(f"转换关系对象时出错: {str(e)}")
                # 尝试创建一个最小的有效关系字典
                try:
                    if (hasattr(relation, 'source') and hasattr(relation, 'target')) or \
                       (isinstance(relation, dict) and 'source' in relation and 'target' in relation):
                        source_text = ''
                        target_text = ''
                        
                        if hasattr(relation, 'source'):
                            source = getattr(relation, 'source')
                            source_text = getattr(source, 'text', str(source)) if hasattr(source, 'text') else str(source)
                        elif isinstance(relation, dict) and 'source' in relation:
                            source = relation['source']
                            source_text = source.get('text', str(source)) if isinstance(source, dict) else str(source)
                            
                        if hasattr(relation, 'target'):
                            target = getattr(relation, 'target')
                            target_text = getattr(target, 'text', str(target)) if hasattr(target, 'text') else str(target)
                        elif isinstance(relation, dict) and 'target' in relation:
                            target = relation['target']
                            target_text = target.get('text', str(target)) if isinstance(target, dict) else str(target)
                        
                        relation_type = getattr(relation, 'type', '') if hasattr(relation, 'type') else \
                                       relation.get('type', '') if isinstance(relation, dict) else ''
                        
                        relation_dict = {
                            'id': str(uuid.uuid4()),
                            'type': relation_type,
                            'source': {'text': source_text},
                            'target': {'text': target_text},
                            'confidence': 0.5,
                            'metadata': {}
                        }
                        relation_dicts.append(relation_dict)
                except:
                    pass
                    
        return relation_dicts

    def _save_training_data(self, formatted_data: Dict[str, Any], scenario_type: str) -> None:
        """保存训练数据到指定目录
        
        Args:
            formatted_data: 格式化后的数据
            scenario_type: 场景类型
        """
        try:
            # 创建训练数据目录
            training_data_dir = os.path.join("output", "training_data")
            os.makedirs(training_data_dir, exist_ok=True)
            
            # 创建场景子目录
            scenario_dir = os.path.join(training_data_dir, scenario_type.lower())
            os.makedirs(scenario_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            filename = f"{scenario_type.lower()}_{timestamp}_{file_id}.json"
            
            # 构建训练数据格式
            training_data = {
                "instruction": self._generate_instruction(scenario_type),
                "input": formatted_data.get("input", {}),
                "output": formatted_data.get("output", {})
            }
            
            # 保存到文件
            file_path = os.path.join(scenario_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"训练数据已保存到: {file_path}")
        except Exception as e:
            self.logger.error(f"保存训练数据失败: {str(e)}")
    
    def _generate_instruction(self, scenario_type: str) -> str:
        """根据场景类型生成指令
        
        Args:
            scenario_type: 场景类型
            
        Returns:
            指令文本
        """
        if scenario_type.lower() == "customer_service":
            return "你是一名专业的客服代表。根据客户的问题和提供的信息，给出专业、有帮助的回答。"
        elif scenario_type.lower() == "fraud_detection":
            return "你是一名金融风控专家。根据交易信息和账户数据，分析是否存在欺诈风险，并给出风险等级和处理建议。"
        elif scenario_type.lower() == "compliance":
            return "你是一名合规专家。根据提供的文档和信息，评估是否符合相关法规和政策，并提出合规建议。"
        else:
            return "根据提供的信息，完成相应的任务。"