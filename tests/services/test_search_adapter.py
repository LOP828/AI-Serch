from app.schemas.search import SearchResultSchema
from app.services.search_adapter import StaticSearchAdapter, deduplicate_search_results


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
