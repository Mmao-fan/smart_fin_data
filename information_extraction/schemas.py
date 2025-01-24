# schemas.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class FinancialEntity(BaseModel):
    text: str
    label: str  # "AMOUNT", "ACCOUNT", "LAW_CLAUSE"等
    start_pos: int
    end_pos: int
    confidence: float = 1.0

class EntityRelation(BaseModel):
    source: FinancialEntity
    target: FinancialEntity
    relation_type: str  # "TRANSFER_TO", "VIOLATES"等

class ProcessedChunk(BaseModel):
    chunk_id: int
    original_text: str
    entities: List[FinancialEntity]
    relations: List[EntityRelation]
    summary: Optional[str]
    anomalies: List[str]