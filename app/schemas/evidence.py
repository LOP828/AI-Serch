from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SupportType(StrEnum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    PARTIAL = "partial"
    NEUTRAL = "neutral"


class EvidenceSchema(BaseModel):
    evidence_id: str
    claim_id: str
    source_id: str
    evidence_text: str
    support_type: SupportType
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_score: float = Field(ge=0.0, le=1.0)
    primary_source_factor: float = Field(gt=0.0)
    recency_factor: float = Field(gt=0.0)
    cross_check_factor: float = Field(gt=0.0)
    conflict_penalty: float = Field(gt=0.0)
    interest_conflict_penalty: float = Field(gt=0.0)
    final_score: float = Field(ge=0.0, le=1.0)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
