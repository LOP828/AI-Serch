from app.schemas.search import SearchResultSchema
from app.services.providers.tavily_provider import TavilyProvider
from app.services.search_provider import SearchProviderErrorCode, SearchProviderResponse


def test_tavily_provider_stub_default_search_returns_controlled_error() -> None:
    provider = TavilyProvider()

    response = provider.search("MiroThinker 1.7", max_results=3)

    assert isinstance(response, SearchProviderResponse)
    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert response.error_message == "TavilyProvider network is disabled in stub."
    assert response.metadata.provider == "tavily"
    assert response.metadata.debug["stub"] is True
    assert response.metadata.debug["network_enabled"] is False
    assert response.metadata.debug["reason"] == "TavilyProvider network is disabled in stub."
    assert response.metadata.debug["query_received"] is True
    assert response.metadata.debug["max_results"] == 3


def test_tavily_provider_stub_does_not_require_api_key() -> None:
    provider = TavilyProvider(api_key=None)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


def test_tavily_provider_stub_allow_network_true_still_does_not_call_network() -> None:
    provider = TavilyProvider(api_key="test-not-real", allow_network=True, timeout_seconds=2.0)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert response.metadata.debug["network_enabled"] is True
    assert response.metadata.debug["timeout_seconds"] == 2.0
    assert response.metadata.debug["fake_client"] is False


def test_tavily_provider_allow_network_false_does_not_call_fake_client() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Should not be called",
                    "url": "https://example.com/should-not-call",
                    "content": "unused",
                }
            ]
        }
    )
    provider = TavilyProvider(allow_network=False, request_func=fake_client)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert fake_client.calls == []


def test_tavily_provider_stub_does_not_expose_api_key_in_debug() -> None:
    provider = TavilyProvider(api_key="test-not-real", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert "api_key" not in response.metadata.debug
    assert "test-not-real" not in repr(response.metadata.debug)


def test_tavily_provider_fake_client_success_returns_normalized_results() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Tavily fake result",
                    "url": "https://example.com/tavily-fake",
                    "content": "Fake Tavily snippet.",
                    "published_date": "2026-05-09",
                    "score": 0.99,
                    "raw_content": "Provider-only raw text.",
                    "provider": "tavily",
                },
                {
                    "title": "Second Tavily fake result",
                    "url": "https://example.com/tavily-fake-2",
                    "content": "Second snippet.",
                },
            ]
        }
    )
    provider = TavilyProvider(
        allow_network=True,
        timeout_seconds=2.5,
        request_func=fake_client,
    )

    response = provider.search("MiroThinker 1.7", max_results=1)

    assert response.error_code is None
    assert len(response.normalized_results) == 1
    result = response.normalized_results[0]
    assert isinstance(result, SearchResultSchema)
    assert result.title == "Tavily fake result"
    assert str(result.url) == "https://example.com/tavily-fake"
    assert result.snippet == "Fake Tavily snippet."
    assert result.published_at == "2026-05-09"
    assert response.metadata.provider == "tavily"
    assert response.metadata.debug["fake_client"] is True
    assert response.metadata.debug["network_enabled"] is True
    assert response.metadata.raw_payload is not None
    assert fake_client.calls == [
        {
            "query": "MiroThinker 1.7",
            "max_results": 1,
            "timeout_seconds": 2.5,
        }
    ]


def test_tavily_provider_fake_client_keeps_provider_fields_out_of_schema() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Provider fields",
                    "url": "https://example.com/provider-fields",
                    "content": "snippet",
                    "score": 0.77,
                    "raw_content": "raw",
                    "provider": "tavily",
                }
            ],
            "request_id": "fake-request",
        }
    )
    provider = TavilyProvider(allow_network=True, request_func=fake_client)

    response = provider.search("query", max_results=1)
    result_data = response.normalized_results[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "score" not in result_data
    assert "raw_content" not in result_data
    assert "provider" not in result_data
    assert "request_id" not in result_data


def test_tavily_provider_fake_client_empty_results_are_valid() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"results": []}),
    )

    response = provider.search("query", max_results=3)

    assert response.normalized_results == []
    assert response.error_code is None


def test_tavily_provider_fake_client_timeout_maps_to_provider_timeout() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RaisingTavilyClient(TimeoutError("fake timeout")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_TIMEOUT
    assert response.metadata.debug["fake_client"] is True


def test_tavily_provider_fake_client_auth_failed_maps_to_provider_auth_failed() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RaisingTavilyClient(FakeHttpError(401, "unauthorized")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED


def test_tavily_provider_fake_client_rate_limit_maps_to_provider_rate_limited() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"status_code": 429, "error": "rate limited"}),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_RATE_LIMITED


def test_tavily_provider_fake_client_quota_maps_to_provider_quota_exceeded() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RecordingTavilyClient(
            payload={"status_code": 429, "error": "quota exhausted"},
        ),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED


def test_tavily_provider_fake_client_bad_payload_maps_to_provider_bad_response() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"results": "not-a-list"}),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_BAD_RESPONSE


def test_tavily_provider_fake_client_generic_exception_maps_to_provider_unavailable() -> None:
    provider = TavilyProvider(
        allow_network=True,
        request_func=RaisingTavilyClient(RuntimeError("fake network unavailable")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


def test_tavily_provider_normalizes_local_payload() -> None:
    payload = {
        "results": [
            {
                "title": "Tavily local payload",
                "url": "https://example.com/tavily-local",
                "content": "Local Tavily snippet.",
                "published_date": "2026-05-08",
                "score": 0.99,
                "raw_content": "Provider-only raw field.",
            }
        ]
    }

    results = TavilyProvider()._normalize_payload(payload)

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SearchResultSchema)
    assert result.title == "Tavily local payload"
    assert str(result.url) == "https://example.com/tavily-local"
    assert result.snippet == "Local Tavily snippet."
    assert result.published_at == "2026-05-08"


def test_tavily_provider_normalized_payload_keeps_provider_fields_out_of_schema() -> None:
    payload = {
        "results": [
            {
                "title": "Provider-only fields",
                "url": "https://example.com/provider-only-fields",
                "content": "snippet",
                "score": 0.7,
                "raw_content": "raw text",
                "provider": "tavily",
            }
        ]
    }

    result_data = TavilyProvider()._normalize_payload(payload)[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "score" not in result_data
    assert "raw_content" not in result_data
    assert "provider" not in result_data


def test_tavily_provider_normalize_payload_respects_max_results() -> None:
    payload = {
        "results": [
            {"title": "One", "url": "https://example.com/one", "content": "one"},
            {"title": "Two", "url": "https://example.com/two", "content": "two"},
        ]
    }

    results = TavilyProvider()._normalize_payload(payload, max_results=1)

    assert [result.title for result in results] == ["One"]


class RecordingTavilyClient:
    def __init__(self, payload):
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    def __call__(self, *, query: str, max_results: int, timeout_seconds: float | None):
        self.calls.append(
            {
                "query": query,
                "max_results": max_results,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self._payload


class RaisingTavilyClient:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def __call__(self, *, query: str, max_results: int, timeout_seconds: float | None):
        del query, max_results, timeout_seconds
        raise self._exc


class FakeHttpError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
