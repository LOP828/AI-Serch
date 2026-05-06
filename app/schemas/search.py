from pydantic import BaseModel, Field, HttpUrl

from app.schemas.source import SourceType


class SearchPlanItemSchema(BaseModel):
    claim_id: str
    queries: list[str] = Field(min_length=1)
    preferred_source_types: list[SourceType] = Field(default_factory=list)


class SearchResultSchema(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    published_at: str | None = None
