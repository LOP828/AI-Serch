from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ErrorResponse
from app.schemas.claim import ClaimSchema
from app.schemas.constraints import AnswerConstraintsSchema
from app.schemas.source import SourceSchema


class QuestionType(StrEnum):
    AUTO = "auto"
    AI_MODEL_INFO = "ai_model_info"
    TECH_NEWS = "tech_news"
    PRODUCT_INFO = "product_info"
    POLICY_LEGAL = "policy_legal"
    TECHNICAL_DOC = "technical_doc"
    GENERAL_FACT = "general_fact"
    UNKNOWN = "unknown"


class Strictness(StrEnum):
    LOOSE = "loose"
    BALANCED = "balanced"
    STRICT = "strict"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OverallStatus(StrEnum):
    CONFIRMED = "confirmed"
    PARTIALLY_CONFIRMED = "partially_confirmed"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"
    FAILED = "failed"


class TrustedSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    question_type: QuestionType = QuestionType.AUTO
    strictness: Strictness = Strictness.BALANCED
    max_sources: int = Field(default=8, ge=1, le=20)
    require_primary_source: bool = False
    return_raw_evidence: bool = True

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized


class TrustedSearchResponse(BaseModel):
    query: str
    question_type: QuestionType
    risk_level: RiskLevel
    overall_status: OverallStatus
    overall_confidence: float = Field(ge=0.0, le=1.0)
    claims: list[ClaimSchema]
    sources: list[SourceSchema]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    answer_constraints: AnswerConstraintsSchema


__all__ = [
    "ErrorResponse",
    "OverallStatus",
    "QuestionType",
    "RiskLevel",
    "Strictness",
    "TrustedSearchRequest",
    "TrustedSearchResponse",
]
