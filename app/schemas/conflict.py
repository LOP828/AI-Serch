from enum import StrEnum

from pydantic import BaseModel, Field


class ConflictSeverity(StrEnum):
    MINOR = "minor"
    MAJOR = "major"


class ConflictSchema(BaseModel):
    conflict_id: str
    claim_id: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    opposing_evidence_ids: list[str] = Field(default_factory=list)
    severity: ConflictSeverity
    summary: str
