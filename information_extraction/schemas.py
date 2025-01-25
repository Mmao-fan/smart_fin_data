# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from pydantic.types import conint

class EntityLabel(str, Enum):
    DATE = "DATE"
    GEO = "GEO"
    ACCOUNT = "ACCOUNT"
    MONEY = "MONEY"
    CREDIT_CARD = "CREDIT_CARD"
    SWIFT_CODE = "SWIFT_CODE"

class FinancialEntity(BaseModel):
    text: str
    label: EntityLabel  # 使用枚举类型
    start_pos: conint(ge=0)  # 非负整数校验
    end_pos: conint(ge=0)
    confidence: float = Field(..., ge=0, le=1.0)

class RelationType(str, Enum):
    TRANSFER_TO = "TRANSFER_TO"
    VIOLATES = "VIOLATES"

class EntityRelation(BaseModel):
    source: FinancialEntity
    target: FinancialEntity
    relation_type: RelationType  # 使用枚举类型

class ProcessedChunk(BaseModel):
    chunk_id: int
    original_text: str
    entities: List[FinancialEntity] = Field(default_factory=list)  # 使用 default_factory
    relations: List[EntityRelation] = Field(default_factory=list)
    summary: Optional[str] = None
    anomalies: List[str] = Field(default_factory=list)