from app.schemas.search import SearchResultSchema
from app.services.search_provider import (
    FakeSearchProvider,
    SearchProviderErrorCode,
    SearchProviderResponse,
)
from tests.services.provider_fixtures import ALL_PROVIDER_ERROR_CODES, provider_debug_payload


def test_fake_search_provider_returns_normalized_results() -> None:
    provider = FakeSearchProvider()

    response = provider.search("MiroThinker 1.7", max_results=1)

    assert isinstance(response, SearchProviderResponse)
    assert response.error_code is None
    assert response.error_message is None
    assert len(response.normalized_results) == 1
    result = response.normalized_results[0]
    assert isinstance(result, SearchResultSchema)
    assert result.title == "Fake provider model card"
    assert str(result.url) == "https://example.com/fake-model-card"
    assert result.snippet
    assert result.published_at is None


def test_normalized_results_do_not_include_provider_metadata() -> None:
    provider = FakeSearchProvider(
        provider_name="fake-provider",
        fallback_used=True,
        raw_payload={"provider": "fake-provider", "private_score": 0.91},
        debug={"request_id": "debug-1"},
    )

    response = provider.search("query", max_results=1)
    result_data = response.normalized_results[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "provider" not in result_data
    assert "fallback_used" not in result_data
    assert "raw_payload" not in result_data
    assert response.metadata.provider == "fake-provider"
    assert response.metadata.fallback_used is True
    assert response.metadata.raw_payload == {"provider": "fake-provider", "private_score": 0.91}
    assert response.metadata.debug == {"request_id": "debug-1"}


def test_provider_failure_returns_controlled_error_response() -> None:
    provider = FakeSearchProvider(
        error_code=SearchProviderErrorCode.PROVIDER_RATE_LIMITED,
        error_message="rate limit reached",
    )

    response = provider.search("query", max_results=8)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_RATE_LIMITED
    assert response.error_message == "rate limit reached"
    assert response.metadata.provider == "fake"


def test_empty_results_are_valid_response() -> None:
    provider = FakeSearchProvider(results=[])

    response = provider.search("query", max_results=8)

    assert response.normalized_results == []
    assert response.error_code is None
    assert response.metadata.provider == "fake"


def test_fake_provider_respects_max_results_and_records_input() -> None:
    results = [
        SearchResultSchema(title="One", url="https://example.com/one", snippet="one"),
        SearchResultSchema(title="Two", url="https://example.com/two", snippet="two"),
        SearchResultSchema(title="Three", url="https://example.com/three", snippet="three"),
    ]
    provider = FakeSearchProvider(results=results)

    response = provider.search("provider boundary", max_results=2)

    assert [result.title for result in response.normalized_results] == ["One", "Two"]
    assert provider.queries == ["provider boundary"]
    assert provider.max_results_values == [2]


def test_provider_error_codes_cover_required_failure_modes() -> None:
    assert {error_code.value for error_code in SearchProviderErrorCode} == {
        "provider_timeout",
        "provider_auth_failed",
        "provider_rate_limited",
        "provider_quota_exceeded",
        "provider_bad_response",
        "provider_unavailable",
    }


def test_fallback_metadata_is_separate_from_normalized_result() -> None:
    provider = FakeSearchProvider(fallback_used=True, debug={"fallback_reason": "timeout"})

    response = provider.search("query", max_results=1)
    result_data = response.normalized_results[0].model_dump()

    assert response.metadata.fallback_used is True
    assert response.metadata.debug == {"fallback_reason": "timeout"}
    assert "fallback_reason" not in result_data


def test_fake_provider_can_return_each_controlled_error_code() -> None:
    for error_code in ALL_PROVIDER_ERROR_CODES:
        provider = FakeSearchProvider(
            error_code=error_code,
            error_message=f"{error_code.value} fixture",
        )

        response = provider.search("query", max_results=8)

        assert response.normalized_results == []
        assert response.error_code == error_code
        assert response.error_message == f"{error_code.value} fixture"
        assert response.metadata.provider == "fake"


def test_provider_error_response_keeps_metadata_and_debug_separate() -> None:
    debug = provider_debug_payload()
    provider = FakeSearchProvider(
        error_code=SearchProviderErrorCode.PROVIDER_BAD_RESPONSE,
        error_message="bad provider payload",
        fallback_used=True,
        raw_payload={"private_score": 0.42, "provider": "fake"},
        debug=debug,
    )

    response = provider.search("query", max_results=8)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_BAD_RESPONSE
    assert response.metadata.fallback_used is True
    assert response.metadata.raw_payload == {"private_score": 0.42, "provider": "fake"}
    assert response.metadata.debug == debug
