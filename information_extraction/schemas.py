# schemas.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto
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
    id: str
    text: str
    type: str
    start: int
    end: int
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.confidence is None:
            self.confidence = 0.0

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
class Relation:
    """关系类"""
    id: str
    type: str
    source: Entity
    target: Entity
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.confidence is None:
            self.confidence = 0.0

@dataclass
class ComplianceEvent:
    """合规事件类"""
    type: str
    text: str
    importance: float
    subtype: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class ProcessedChunk:
    """处理后的文本块"""
    chunk_id: int
    original_text: str
    entities: List[Entity]
    relations: List[Relation]
    summary: Optional[str] = None
    anomalies: Optional[List[Dict]] = None
    qa_pairs: Optional[List[Dict]] = None
    compliance_events: Optional[List[ComplianceEvent]] = None
    compliance_analysis: Optional[Dict] = None