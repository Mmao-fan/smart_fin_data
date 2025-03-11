# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum, auto
from pydantic.types import conint
from dataclasses import dataclass
from datetime import datetime

class EntityLabel(str, Enum):
    """实体标签枚举"""
    PERSON = "PERSON"
    ORG = "ORG"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    DATE = "DATE"
    TIME = "TIME"
    LOCATION = "LOCATION"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ID = "ID"
    BANK = "BANK"
    ACCOUNT = "ACCOUNT"
    TRANSACTION_TYPE = "TRANSACTION_TYPE"
    TERM = "TERM"

class RelationType(str, Enum):
    """关系类型枚举"""
    TRANSFER_TO = "TRANSFER_TO"
    BELONGS_TO = "BELONGS_TO"
    PART_OF = "PART_OF"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    OCCURRED_AT = "OCCURRED_AT"
    HAS_AMOUNT = "HAS_AMOUNT"

@dataclass
class Entity:
    """实体类"""
    type: str  # 实体类型
    text: str  # 实体文本
    start: int  # 开始位置
    end: int   # 结束位置
    
    @property
    def label(self) -> str:
        """兼容性属性，返回实体类型"""
        return self.type
    
    @property
    def start_pos(self) -> int:
        """兼容性属性，返回开始位置"""
        return self.start
    
    @property
    def end_pos(self) -> int:
        """兼容性属性，返回结束位置"""
        return self.end

@dataclass
class ComplianceEvent:
    """合规事件类"""
    type: str
    text: str
    start: int
    end: int
    importance: str
    subtype: Optional[str] = None

@dataclass
class ProcessedChunk:
    """处理后的文本块"""
    chunk_id: int
    original_text: str
    entities: List[Entity]
    relations: List[Dict[str, Any]]
    summary: Optional[str] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    qa_pairs: Optional[List[Dict[str, str]]] = None
    compliance_events: Optional[List[ComplianceEvent]] = None
    compliance_analysis: Optional[Dict[str, Any]] = None

class FinancialEntity(BaseModel):
    """金融实体模型"""
    text: str
    label: EntityLabel
    start_pos: int
    end_pos: int
    confidence: float = Field(..., ge=0, le=1)

class Relation(BaseModel):
    """关系模型"""
    source: Entity
    target: Entity
    relation_type: str
    confidence: float = Field(..., ge=0, le=1)

class EntityRelation(BaseModel):
    """实体关系模型"""
    source: FinancialEntity
    target: FinancialEntity
    relation_type: RelationType
    confidence: float = Field(default=1.0, ge=0, le=1)

class Anomaly(BaseModel):
    """异常模型"""
    type: str
    description: str
    entities: List[Entity]
    confidence: float = Field(..., ge=0, le=1)
    context: Optional[str] = None