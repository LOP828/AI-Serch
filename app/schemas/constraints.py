from enum import StrEnum

from pydantic import BaseModel, Field


class AllowedTone(StrEnum):
    CONFIDENT = "confident"
    CAUTIOUS = "cautious"
    NEUTRAL = "neutral"


class AnswerConstraintsSchema(BaseModel):
    can_answer_confidently: bool
    must_disclose_uncertainty: bool
    must_cite_sources: bool
    allowed_tone: AllowedTone
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
