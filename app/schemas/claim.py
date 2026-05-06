from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceSchema


class ClaimStatus(StrEnum):
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"
    FALSE_LIKELY = "false_likely"


class ClaimSchema(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str
    status: ClaimStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[EvidenceSchema] = Field(default_factory=list)
