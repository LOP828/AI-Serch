from pydantic import BaseModel, HttpUrl

from app.schemas.source import FetchStatus


class PageFetchResultSchema(BaseModel):
    url: HttpUrl
    title: str | None = None
    text: str
    fetch_status: FetchStatus
    error_message: str | None = None
    fetched_at: str | None = None
