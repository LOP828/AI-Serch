from collections.abc import Mapping
from typing import Any

from app.schemas.search import SearchResultSchema
from app.services.search_provider import (
    SearchProviderErrorCode,
    SearchProviderMetadata,
    SearchProviderResponse,
)
from app.services.search_provider_normalizer import normalize_tavily_results


class TavilyProvider:
    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        allow_network: bool = False,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._allow_network = allow_network

    def search(self, query: str, max_results: int) -> SearchProviderResponse:
        metadata = SearchProviderMetadata(
            provider="tavily",
            debug={
                "stub": True,
                "network_enabled": self._allow_network,
                "reason": "TavilyProvider network is disabled in stub.",
                "query_received": bool(query),
                "max_results": max_results,
                "timeout_seconds": self._timeout_seconds,
            },
        )
        return SearchProviderResponse(
            normalized_results=[],
            metadata=metadata,
            error_code=SearchProviderErrorCode.PROVIDER_UNAVAILABLE,
            error_message="TavilyProvider network is disabled in stub.",
        )

    def _normalize_payload(
        self,
        raw_payload: Mapping[str, Any],
        max_results: int | None = None,
    ) -> list[SearchResultSchema]:
        return normalize_tavily_results(raw_payload, max_results=max_results)
