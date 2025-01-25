# schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class DialogRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class IntentType(str, Enum):
    CARD_FRAUD = "card_fraud"
    BALANCE_QUERY = "balance_query"
    OTHER = "other"

class DialogTurn(BaseModel):
    role: DialogRole  # 严格使用枚举类型
    content: str
    intent: IntentType = IntentType.OTHER
    confidence: float = Field(..., ge=0, le=1.0)

class TransactionGraphNode(BaseModel):
    node_id: str
    node_type: str = Field(..., pattern=r"^(account|transaction|location)$")
    properties: Dict[str, str] = Field(default_factory=dict)

class TransactionGraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = Field(..., pattern=r"^(initiated|sent_to|located_in)$")
    properties: Dict[str, str] = Field(default_factory=dict)

class ComplianceClause(BaseModel):
    original_text: str
    summary: Optional[str] = None
    obligations: List[Dict[str, str]] = Field(default_factory=list)
    law_references: List[str] = Field(default_factory=list)