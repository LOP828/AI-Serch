from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class SourceType(StrEnum):
    OFFICIAL_DOCS = "official_docs"
    OFFICIAL_BLOG = "official_blog"
    OFFICIAL_MODEL_CARD = "official_model_card"
    SOURCE_CODE_REPO = "source_code_repo"
    ACADEMIC_PAPER = "academic_paper"
    FINANCIAL_FILING = "financial_filing"
    GOVERNMENT_DOCS = "government_docs"
    MAINSTREAM_MEDIA = "mainstream_media"
    EXPERT_BLOG = "expert_blog"
    COMMUNITY_FORUM = "community_forum"
    PRODUCT_PAGE = "product_page"
    SEO_CONTENT = "seo_content"
    UNKNOWN = "unknown"


class FetchStatus(StrEnum):
    SUCCESS = "success"
    FALLBACK = "fallback"
    FAILED = "failed"
    FALLBACK_SNIPPET = "fallback_snippet"
    TIMEOUT = "timeout"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"
    BLOCKED = "blocked"
    NOT_FETCHED = "not_fetched"


class SourceSchema(BaseModel):
    source_id: str
    title: str
    url: HttpUrl
    domain: str
    snippet: str | None = None
    source_type: SourceType
    base_reliability: float = Field(ge=0.0, le=1.0)
    is_primary_source: bool
    published_at: str | None = None
    author: str | None = None
    fetched_at: str | None = None
    fetch_status: FetchStatus | None = None
