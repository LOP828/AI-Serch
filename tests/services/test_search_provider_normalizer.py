from app.schemas.search import SearchResultSchema
from app.services.search_provider_normalizer import (
    normalize_brave_results,
    normalize_serpapi_results,
    normalize_tavily_results,
)


def test_tavily_payload_maps_to_search_result_schema() -> None:
    payload = {
        "results": [
            {
                "title": "Tavily model card",
                "url": "https://example.com/tavily-model",
                "content": "Tavily content summary.",
                "published_date": "2026-01-02",
                "score": 0.92,
                "raw_content": "Provider-only raw content.",
            }
        ]
    }

    results = normalize_tavily_results(payload)

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SearchResultSchema)
    assert result.title == "Tavily model card"
    assert str(result.url) == "https://example.com/tavily-model"
    assert result.snippet == "Tavily content summary."
    assert result.published_at == "2026-01-02"


def test_brave_payload_maps_to_search_result_schema() -> None:
    payload = {
        "web": {
            "results": [
                {
                    "title": "Brave web result",
                    "url": "https://example.com/brave-result",
                    "description": "Brave result description.",
                    "age": "2 days ago",
                    "profile": {"name": "provider-only"},
                }
            ]
        }
    }

    results = normalize_brave_results(payload)

    assert len(results) == 1
    result = results[0]
    assert result.title == "Brave web result"
    assert str(result.url) == "https://example.com/brave-result"
    assert result.snippet == "Brave result description."
    assert result.published_at is None


def test_serpapi_payload_maps_to_search_result_schema() -> None:
    payload = {
        "organic_results": [
            {
                "title": "SerpAPI organic result",
                "link": "https://example.com/serpapi-result",
                "snippet": "SerpAPI organic snippet.",
                "date": "2025-12-31",
                "source": "provider-only source",
            }
        ]
    }

    results = normalize_serpapi_results(payload)

    assert len(results) == 1
    result = results[0]
    assert result.title == "SerpAPI organic result"
    assert str(result.url) == "https://example.com/serpapi-result"
    assert result.snippet == "SerpAPI organic snippet."
    assert result.published_at == "2025-12-31"


def test_missing_snippet_uses_empty_string() -> None:
    payload = {"results": [{"title": "No snippet", "url": "https://example.com/no-snippet"}]}

    results = normalize_tavily_results(payload)

    assert results[0].snippet == ""


def test_missing_published_at_is_none() -> None:
    payload = {"results": [{"title": "No date", "url": "https://example.com/no-date"}]}

    results = normalize_tavily_results(payload)

    assert results[0].published_at is None


def test_empty_url_and_empty_title_are_filtered() -> None:
    payload = {
        "organic_results": [
            {"title": "Missing URL", "link": "", "snippet": "drop"},
            {"title": "", "link": "https://example.com/missing-title", "snippet": "drop"},
            {"title": "Valid", "link": "https://example.com/valid", "snippet": "keep"},
        ]
    }

    results = normalize_serpapi_results(payload)

    assert [result.title for result in results] == ["Valid"]


def test_invalid_url_is_filtered() -> None:
    payload = {
        "web": {
            "results": [
                {"title": "Invalid URL", "url": "not-a-url", "description": "drop"},
                {"title": "Valid URL", "url": "https://example.com/valid", "description": "keep"},
            ]
        }
    }

    results = normalize_brave_results(payload)

    assert [result.title for result in results] == ["Valid URL"]


def test_duplicate_urls_are_deduplicated_with_first_result_kept() -> None:
    payload = {
        "results": [
            {
                "title": "First",
                "url": "https://example.com/page?utm_source=test",
                "content": "first",
            },
            {
                "title": "Duplicate",
                "url": "https://example.com/page#section",
                "content": "duplicate",
            },
        ]
    }

    results = normalize_tavily_results(payload)

    assert [result.title for result in results] == ["First"]


def test_provider_specific_fields_do_not_enter_search_result_schema() -> None:
    payload = {
        "results": [
            {
                "title": "Provider fields",
                "url": "https://example.com/provider-fields",
                "content": "snippet",
                "score": 0.8,
                "raw_content": "raw provider text",
                "provider": "tavily",
            }
        ]
    }

    result_data = normalize_tavily_results(payload)[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "score" not in result_data
    assert "raw_content" not in result_data
    assert "provider" not in result_data


def test_raw_payload_does_not_enter_search_result_schema() -> None:
    payload = {
        "organic_results": [
            {
                "title": "Raw payload",
                "link": "https://example.com/raw-payload",
                "snippet": "snippet",
                "raw_payload": {"private": True},
            }
        ]
    }

    result_data = normalize_serpapi_results(payload)[0].model_dump()

    assert "raw_payload" not in result_data


def test_max_results_limits_normalized_output() -> None:
    payload = {
        "web": {
            "results": [
                {"title": "One", "url": "https://example.com/one", "description": "one"},
                {"title": "Two", "url": "https://example.com/two", "description": "two"},
            ]
        }
    }

    results = normalize_brave_results(payload, max_results=1)

    assert [result.title for result in results] == ["One"]


def test_non_list_or_missing_provider_sections_return_empty_results() -> None:
    assert normalize_tavily_results({"results": {"bad": "shape"}}) == []
    assert normalize_brave_results({"web": {"results": {"bad": "shape"}}}) == []
    assert normalize_brave_results({"no_web": []}) == []
    assert normalize_serpapi_results({"organic_results": {"bad": "shape"}}) == []
