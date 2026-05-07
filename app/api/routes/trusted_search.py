from fastapi import APIRouter

from app.schemas.trusted_search import TrustedSearchRequest, TrustedSearchResponse
from app.services.trusted_search_service import TrustedSearchService

router = APIRouter(prefix="/api/v1", tags=["trusted-search"])


@router.post("/trusted-search", response_model=TrustedSearchResponse)
async def trusted_search(request: TrustedSearchRequest) -> TrustedSearchResponse:
    return TrustedSearchService().search(request)
