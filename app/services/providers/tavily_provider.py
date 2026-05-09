from collections.abc import Callable, Mapping
from typing import Any

from app.schemas.search import SearchResultSchema
from app.services.search_provider import (
    SearchProviderErrorCode,
    SearchProviderMetadata,
    SearchProviderResponse,
)
from app.services.search_provider_normalizer import normalize_tavily_results

TavilyRequestFunc = Callable[..., Mapping[str, Any]]


class TavilyProvider:
    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        allow_network: bool = False,
        request_func: TavilyRequestFunc | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._allow_network = allow_network
        self._request_func = request_func

    def search(self, query: str, max_results: int) -> SearchProviderResponse:
        if not self._allow_network:
            return self._error_response(
                query=query,
                max_results=max_results,
                error_code=SearchProviderErrorCode.PROVIDER_UNAVAILABLE,
                error_message="TavilyProvider network is disabled in stub.",
                reason="TavilyProvider network is disabled in stub.",
                stub=True,
            )

        if self._request_func is None:
            return self._error_response(
                query=query,
                max_results=max_results,
                error_code=SearchProviderErrorCode.PROVIDER_UNAVAILABLE,
                error_message="TavilyProvider requires an injected request function.",
                reason="No request function is configured; real network access is not enabled.",
                stub=True,
            )

        try:
            raw_payload = self._request_func(
                query=query,
                max_results=max_results,
                timeout_seconds=self._timeout_seconds,
            )
        except Exception as exc:
            return self._exception_response(query, max_results, exc)

        if not isinstance(raw_payload, Mapping):
            return self._error_response(
                query=query,
                max_results=max_results,
                error_code=SearchProviderErrorCode.PROVIDER_BAD_RESPONSE,
                error_message="TavilyProvider received a non-object payload.",
                reason="Provider payload is not a mapping.",
                fake_client=True,
            )

        error_code = self._error_code_from_payload(raw_payload)
        if error_code is not None:
            return self._error_response(
                query=query,
                max_results=max_results,
                error_code=error_code,
                error_message=f"TavilyProvider fake client returned {error_code.value}.",
                reason="Provider payload contains an error status.",
                fake_client=True,
                raw_payload=dict(raw_payload),
            )

        if "results" not in raw_payload or not isinstance(raw_payload.get("results"), list):
            return self._error_response(
                query=query,
                max_results=max_results,
                error_code=SearchProviderErrorCode.PROVIDER_BAD_RESPONSE,
                error_message="TavilyProvider received an invalid results payload.",
                reason="Provider payload results field is missing or invalid.",
                fake_client=True,
                raw_payload=dict(raw_payload),
            )

        normalized_results = self._normalize_payload(raw_payload, max_results=max_results)
        return SearchProviderResponse(
            normalized_results=normalized_results,
            metadata=self._metadata(
                query=query,
                max_results=max_results,
                fake_client=True,
                raw_payload=dict(raw_payload),
            ),
        )

    def _normalize_payload(
        self,
        raw_payload: Mapping[str, Any],
        max_results: int | None = None,
    ) -> list[SearchResultSchema]:
        return normalize_tavily_results(raw_payload, max_results=max_results)

    def _metadata(
        self,
        query: str,
        max_results: int,
        *,
        reason: str | None = None,
        stub: bool = False,
        fake_client: bool = False,
        raw_payload: dict[str, Any] | None = None,
        error_type: str | None = None,
    ) -> SearchProviderMetadata:
        debug: dict[str, Any] = {
            "stub": stub,
            "network_enabled": self._allow_network,
            "fake_client": fake_client,
            "query_received": bool(query),
            "max_results": max_results,
            "timeout_seconds": self._timeout_seconds,
        }
        if reason is not None:
            debug["reason"] = reason
        if error_type is not None:
            debug["error_type"] = error_type

        return SearchProviderMetadata(
            provider="tavily",
            raw_payload=raw_payload,
            debug=debug,
        )

    def _error_response(
        self,
        *,
        query: str,
        max_results: int,
        error_code: SearchProviderErrorCode,
        error_message: str,
        reason: str,
        stub: bool = False,
        fake_client: bool = False,
        raw_payload: dict[str, Any] | None = None,
    ) -> SearchProviderResponse:
        return SearchProviderResponse(
            normalized_results=[],
            metadata=self._metadata(
                query=query,
                max_results=max_results,
                reason=reason,
                stub=stub,
                fake_client=fake_client,
                raw_payload=raw_payload,
                error_type=error_code.value,
            ),
            error_code=error_code,
            error_message=error_message,
        )

    def _exception_response(
        self,
        query: str,
        max_results: int,
        exc: Exception,
    ) -> SearchProviderResponse:
        error_code = self._error_code_from_exception(exc)
        return self._error_response(
            query=query,
            max_results=max_results,
            error_code=error_code,
            error_message=f"TavilyProvider request failed with {error_code.value}.",
            reason=type(exc).__name__,
            fake_client=True,
        )

    def _error_code_from_exception(self, exc: Exception) -> SearchProviderErrorCode:
        if isinstance(exc, TimeoutError):
            return SearchProviderErrorCode.PROVIDER_TIMEOUT

        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return self._error_code_from_status(status_code, str(exc))

        return SearchProviderErrorCode.PROVIDER_UNAVAILABLE

    def _error_code_from_payload(
        self,
        raw_payload: Mapping[str, Any],
    ) -> SearchProviderErrorCode | None:
        explicit_error = raw_payload.get("error_code")
        if isinstance(explicit_error, str):
            for error_code in SearchProviderErrorCode:
                if explicit_error == error_code.value:
                    return error_code

        status_code = raw_payload.get("status_code")
        if isinstance(status_code, int) and status_code >= 400:
            return self._error_code_from_status(status_code, str(raw_payload.get("error", "")))

        return None

    def _error_code_from_status(self, status_code: int, message: str) -> SearchProviderErrorCode:
        message_lower = message.lower()
        if status_code in {401, 403}:
            return SearchProviderErrorCode.PROVIDER_AUTH_FAILED
        if status_code == 429:
            if "quota" in message_lower or "credit" in message_lower or "exhaust" in message_lower:
                return SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED
            return SearchProviderErrorCode.PROVIDER_RATE_LIMITED
        if status_code == 402:
            return SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED
        if 500 <= status_code <= 599:
            return SearchProviderErrorCode.PROVIDER_UNAVAILABLE
        return SearchProviderErrorCode.PROVIDER_BAD_RESPONSE
