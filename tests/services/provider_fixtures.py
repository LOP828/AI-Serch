from app.schemas.search import SearchResultSchema
from app.services.search_provider import SearchProviderErrorCode

ALL_PROVIDER_ERROR_CODES = (
    SearchProviderErrorCode.PROVIDER_TIMEOUT,
    SearchProviderErrorCode.PROVIDER_AUTH_FAILED,
    SearchProviderErrorCode.PROVIDER_RATE_LIMITED,
    SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED,
    SearchProviderErrorCode.PROVIDER_BAD_RESPONSE,
    SearchProviderErrorCode.PROVIDER_UNAVAILABLE,
)


def provider_results(count: int = 3) -> list[SearchResultSchema]:
    return [
        SearchResultSchema(
            title=f"Provider fixture result {index}",
            url=f"https://example.com/provider-fixture-{index}",
            snippet=f"Provider fixture snippet {index}.",
            published_at=None,
        )
        for index in range(1, count + 1)
    ]


def provider_debug_payload() -> dict[str, object]:
    return {
        "request_id": "fixture-request-id",
        "duration_ms": 123,
        "retry_after_seconds": 30,
    }
