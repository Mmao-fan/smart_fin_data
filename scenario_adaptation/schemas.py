# schemas.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class DialogTurn(BaseModel):
    """对话轮次数据结构"""
    role: str  # "user"或"assistant"
    content: str
    intent: str  # 场景意图分类
    confidence: float = 1.0

class TransactionGraphNode(BaseModel):
    """交易图谱节点定义"""
    node_id: str
    node_type: str  # "account", "transaction", "location"
    properties: Dict[str, str]

class TransactionGraphEdge(BaseModel):
    """交易图谱边定义"""
    source_id: str
    target_id: str
    relation_type: str  # "TRANSFER_TO", "LOCATED_IN"等
    properties: Dict[str, str]

class ComplianceClause(BaseModel):
    """合规条款映射数据"""
    original_text: str
    summary: str
    obligations: List[Dict[str, str]]
    law_references: List[str]