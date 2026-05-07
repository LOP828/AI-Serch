from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from app.schemas.search import SearchResultSchema


class SearchProviderErrorCode(StrEnum):
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_AUTH_FAILED = "provider_auth_failed"
    PROVIDER_RATE_LIMITED = "provider_rate_limited"
    PROVIDER_QUOTA_EXCEEDED = "provider_quota_exceeded"
    PROVIDER_BAD_RESPONSE = "provider_bad_response"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


@dataclass(frozen=True)
class SearchProviderMetadata:
    provider: str
    fallback_used: bool = False
    raw_payload: dict[str, Any] | None = None
    debug: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchProviderResponse:
    normalized_results: list[SearchResultSchema]
    metadata: SearchProviderMetadata
    error_code: SearchProviderErrorCode | None = None
    error_message: str | None = None


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int) -> SearchProviderResponse:
        """Return normalized results and metadata without raising provider errors."""


class FakeSearchProvider:
    """Deterministic provider for tests; never performs network or credential access."""

    def __init__(
        self,
        results: list[SearchResultSchema] | None = None,
        provider_name: str = "fake",
        error_code: SearchProviderErrorCode | None = None,
        error_message: str | None = None,
        fallback_used: bool = False,
        raw_payload: dict[str, Any] | None = None,
        debug: dict[str, Any] | None = None,
    ) -> None:
        self._results = results if results is not None else _default_fake_results()
        self._provider_name = provider_name
        self._error_code = error_code
        self._error_message = error_message
        self._fallback_used = fallback_used
        self._raw_payload = raw_payload
        self._debug = debug or {}
        self.queries: list[str] = []
        self.max_results_values: list[int] = []

    def search(self, query: str, max_results: int) -> SearchProviderResponse:
        self.queries.append(query)
        self.max_results_values.append(max_results)
        metadata = SearchProviderMetadata(
            provider=self._provider_name,
            fallback_used=self._fallback_used,
            raw_payload=self._raw_payload,
            debug=self._debug,
        )
        if self._error_code is not None:
            return SearchProviderResponse(
                normalized_results=[],
                metadata=metadata,
                error_code=self._error_code,
                error_message=self._error_message,
            )

        return SearchProviderResponse(
            normalized_results=self._results[:max_results],
            metadata=metadata,
        )


def _default_fake_results() -> list[SearchResultSchema]:
    return [
        SearchResultSchema(
            title="Fake provider model card",
            url="https://example.com/fake-model-card",
            snippet="A fake normalized result used for provider boundary tests.",
            published_at=None,
        ),
        SearchResultSchema(
            title="Fake provider repository",
            url="https://example.com/fake-repository",
            snippet="A second fake normalized result used to verify max_results.",
            published_at=None,
        ),
    ]
