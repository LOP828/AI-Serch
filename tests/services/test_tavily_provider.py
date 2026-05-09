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


def test_tavily_provider_stub_does_not_expose_api_key_in_debug() -> None:
    provider = TavilyProvider(api_key="test-not-real", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert "api_key" not in response.metadata.debug
    assert "test-not-real" not in repr(response.metadata.debug)


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
