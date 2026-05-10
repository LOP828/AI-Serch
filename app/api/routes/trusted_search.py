from fastapi import APIRouter

from app.schemas.trusted_search import TrustedSearchRequest, TrustedSearchResponse
from app.services.search_provider_factory import build_search_adapter
from app.services.trusted_search_service import TrustedSearchService

router = APIRouter(prefix="/api/v1", tags=["trusted-search"])


@router.post("/trusted-search", response_model=TrustedSearchResponse)
async def trusted_search(request: TrustedSearchRequest) -> TrustedSearchResponse:
    search_adapter = build_search_adapter()
    service = TrustedSearchService(search_adapter=search_adapter)
    return service.search(request)
