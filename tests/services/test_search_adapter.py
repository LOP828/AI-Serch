from app.schemas.search import SearchResultSchema
from app.services.search_adapter import StaticSearchAdapter, deduplicate_search_results
from app.services.search_provider import (
    FakeSearchProvider,
    SearchProviderErrorCode,
    SearchProviderMetadata,
    SearchProviderResponse,
)
from tests.services.provider_fixtures import ALL_PROVIDER_ERROR_CODES, provider_results


def test_static_search_adapter_returns_normalized_result_fields() -> None:
    response = StaticSearchAdapter().search("MiroThinker 1.7", max_results=1)

    assert response.error is None
    assert len(response.results) == 1
    result = response.results[0]
    assert result.title
    assert str(result.url).startswith("https://")
    assert result.snippet


def test_search_result_deduplication_keeps_stable_order() -> None:
    results = [
        SearchResultSchema(
            title="First",
            url="https://example.com/a?utm_source=test",
            snippet="first",
        ),
        SearchResultSchema(
            title="Duplicate",
            url="https://example.com/a#section",
            snippet="duplicate",
        ),
        SearchResultSchema(
            title="Second",
            url="https://example.com/b",
            snippet="second",
        ),
    ]

    deduplicated = deduplicate_search_results(results)

    assert [result.title for result in deduplicated] == ["First", "Second"]


def test_adapter_failure_returns_controlled_empty_response() -> None:
    response = StaticSearchAdapter(should_fail=True).search("MiroThinker 1.7")

    assert response.results == []
    assert response.error == "mock_search_failure"


def test_static_search_adapter_default_behavior_stays_static_without_provider() -> None:
    response = StaticSearchAdapter().search("query", max_results=2)

    assert response.error is None
    assert [result.title for result in response.results] == [
        "MiroThinker-1.7 - Hugging Face",
        "MiroThinker GitHub repository",
    ]


def test_static_search_adapter_uses_injected_provider_normalized_results() -> None:
    provider = FakeSearchProvider(
        results=[
            SearchResultSchema(
                title="Provider result",
                url="https://example.com/provider-result",
                snippet="provider snippet",
                published_at=None,
            )
        ],
        provider_name="fake-provider",
        raw_payload={"provider": "fake-provider", "score": 0.91},
    )

    response = StaticSearchAdapter(provider=provider).search("provider query", max_results=8)

    assert response.error is None
    assert len(response.results) == 1
    assert response.results[0].title == "Provider result"
    assert provider.queries == ["provider query"]
    assert provider.max_results_values == [8]


def test_provider_metadata_does_not_enter_search_result_schema() -> None:
    provider = FakeSearchProvider(
        fallback_used=True,
        raw_payload={"provider": "fake", "raw": "payload"},
        debug={"fallback_reason": "provider_timeout"},
    )

    response = StaticSearchAdapter(provider=provider).search("query", max_results=1)
    result_data = response.results[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "provider" not in result_data
    assert "fallback_used" not in result_data
    assert "raw_payload" not in result_data
    assert response.error is None


def test_provider_empty_results_return_controlled_empty_adapter_response() -> None:
    response = StaticSearchAdapter(provider=FakeSearchProvider(results=[])).search(
        "query",
        max_results=8,
    )

    assert response.results == []
    assert response.error is None


def test_provider_error_returns_controlled_empty_adapter_response() -> None:
    provider = FakeSearchProvider(error_code=SearchProviderErrorCode.PROVIDER_TIMEOUT)

    response = StaticSearchAdapter(provider=provider).search("query", max_results=8)

    assert response.results == []
    assert response.error == "provider_timeout"


def test_provider_error_codes_are_forwarded_as_controlled_adapter_errors() -> None:
    for error_code in ALL_PROVIDER_ERROR_CODES:
        provider = FakeSearchProvider(error_code=error_code)

        response = StaticSearchAdapter(provider=provider).search("query", max_results=8)

        assert response.results == []
        assert response.error == error_code.value


def test_provider_exception_returns_controlled_empty_adapter_response() -> None:
    response = StaticSearchAdapter(provider=RaisingSearchProvider()).search(
        "query",
        max_results=8,
    )

    assert response.results == []
    assert response.error
    assert response.error.startswith("provider_unavailable")


def test_adapter_provider_path_respects_max_results() -> None:
    provider = FakeSearchProvider(results=provider_results(count=3))

    response = StaticSearchAdapter(provider=provider).search(
        "query",
        max_results=2,
    )

    assert [result.title for result in response.results] == [
        "Provider fixture result 1",
        "Provider fixture result 2",
    ]
    assert provider.max_results_values == [2]


def test_search_many_deduplicates_results_across_queries_with_stable_order() -> None:
    provider = QueryAwareSearchProvider(
        {
            "first": [
                SearchResultSchema(
                    title="First",
                    url="https://example.com/a?utm_source=test",
                    snippet="first",
                ),
                SearchResultSchema(
                    title="Second",
                    url="https://example.com/b",
                    snippet="second",
                ),
            ],
            "second": [
                SearchResultSchema(
                    title="Duplicate",
                    url="https://example.com/a#section",
                    snippet="duplicate",
                ),
                SearchResultSchema(
                    title="Third",
                    url="https://example.com/c",
                    snippet="third",
                ),
            ],
        }
    )

    response = StaticSearchAdapter(provider=provider).search_many(
        ["first", "second"],
        max_results_per_query=2,
        max_total_results=3,
    )

    assert response.error is None
    assert [result.title for result in response.results] == ["First", "Second", "Third"]
    assert provider.queries == ["first", "second"]
    assert provider.max_results_values == [2, 2]


def test_search_many_partial_failure_uses_successful_query_results() -> None:
    provider = QueryAwareSearchProvider(
        {
            "success": [
                SearchResultSchema(
                    title="Successful result",
                    url="https://example.com/success",
                    snippet="success",
                )
            ]
        },
        errors={"timeout": SearchProviderErrorCode.PROVIDER_TIMEOUT},
    )

    response = StaticSearchAdapter(provider=provider).search_many(
        ["timeout", "success"],
        max_results_per_query=1,
        max_total_results=3,
    )

    assert response.error is None
    assert [result.title for result in response.results] == ["Successful result"]
    assert provider.queries == ["timeout", "success"]


def test_search_many_all_failures_returns_controlled_error() -> None:
    provider = QueryAwareSearchProvider(
        {},
        errors={
            "timeout": SearchProviderErrorCode.PROVIDER_TIMEOUT,
            "unavailable": SearchProviderErrorCode.PROVIDER_UNAVAILABLE,
        },
    )

    response = StaticSearchAdapter(provider=provider).search_many(
        ["timeout", "unavailable"],
        max_results_per_query=1,
        max_total_results=3,
    )

    assert response.results == []
    assert response.error == "provider_timeout"


def test_search_many_keeps_legacy_static_path_non_network_and_capped() -> None:
    response = StaticSearchAdapter().search_many(
        ["query one", "query two"],
        max_results_per_query=2,
        max_total_results=1,
    )

    assert response.error is None
    assert [result.title for result in response.results] == ["MiroThinker-1.7 - Hugging Face"]


def test_provider_results_are_capped_even_if_provider_over_returns() -> None:
    provider = OverReturningSearchProvider()

    response = StaticSearchAdapter(provider=provider).search("query", max_results=2)

    assert response.error is None
    assert [result.title for result in response.results] == [
        "Provider fixture result 1",
        "Provider fixture result 2",
    ]


class RaisingSearchProvider:
    def search(self, query: str, max_results: int):
        del query, max_results
        raise RuntimeError("provider failed")


class OverReturningSearchProvider:
    def search(self, query: str, max_results: int):
        del query, max_results
        from app.services.search_provider import SearchProviderMetadata, SearchProviderResponse

        return SearchProviderResponse(
            normalized_results=provider_results(count=4),
            metadata=SearchProviderMetadata(provider="over-returning-fixture"),
        )


class QueryAwareSearchProvider:
    def __init__(
        self,
        results_by_query: dict[str, list[SearchResultSchema]],
        errors: dict[str, SearchProviderErrorCode] | None = None,
    ) -> None:
        self._results_by_query = results_by_query
        self._errors = errors or {}
        self.queries: list[str] = []
        self.max_results_values: list[int] = []

    def search(self, query: str, max_results: int):
        self.queries.append(query)
        self.max_results_values.append(max_results)
        metadata = SearchProviderMetadata(provider="query-aware-fixture")
        error_code = self._errors.get(query)
        if error_code:
            return SearchProviderResponse(
                normalized_results=[],
                metadata=metadata,
                error_code=error_code,
            )
        return SearchProviderResponse(
            normalized_results=self._results_by_query.get(query, [])[:max_results],
            metadata=metadata,
        )
