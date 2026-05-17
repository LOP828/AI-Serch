from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.schemas.search import SearchResultSchema
from app.services.search_provider import SearchProvider


@dataclass(frozen=True)
class SearchAdapterResponse:
    results: list[SearchResultSchema]
    error: str | None = None


class SearchAdapter(Protocol):
    def search(self, query: str, max_results: int = 8) -> SearchAdapterResponse:
        """Return normalized search results without raising provider errors."""

    def search_many(
        self,
        queries: list[str],
        max_results_per_query: int = 8,
        max_total_results: int = 8,
    ) -> SearchAdapterResponse:
        """Return deduplicated normalized search results for multiple queries."""


class StaticSearchAdapter:
    def __init__(
        self,
        results: list[SearchResultSchema] | None = None,
        should_fail: bool = False,
        provider: SearchProvider | None = None,
    ) -> None:
        self._results = results if results is not None else _default_static_results()
        self._should_fail = should_fail
        self._provider = provider

    def search(self, query: str, max_results: int = 8) -> SearchAdapterResponse:
        if self._should_fail:
            return SearchAdapterResponse(results=[], error="mock_search_failure")

        if self._provider is not None:
            try:
                provider_response = self._provider.search(query, max_results)
            except Exception as exc:
                return SearchAdapterResponse(results=[], error=f"provider_unavailable: {exc}")
            if provider_response.error_code is not None:
                return SearchAdapterResponse(results=[], error=provider_response.error_code.value)
            return SearchAdapterResponse(
                results=provider_response.normalized_results[:max_results],
            )

        del query
        deduplicated = deduplicate_search_results(self._results)
        return SearchAdapterResponse(results=deduplicated[:max_results])

    def search_many(
        self,
        queries: list[str],
        max_results_per_query: int = 8,
        max_total_results: int = 8,
    ) -> SearchAdapterResponse:
        selected_queries = _deduplicate_strings([query for query in queries if query.strip()])
        if not selected_queries:
            return SearchAdapterResponse(results=[], error="no_queries")

        collected: list[SearchResultSchema] = []
        errors: list[str] = []
        for query in selected_queries:
            response = self.search(query, max_results=max_results_per_query)
            if response.error:
                errors.append(response.error)
                continue
            collected.extend(response.results)
            collected = deduplicate_search_results(collected)
            if len(collected) >= max_total_results:
                break

        deduplicated = deduplicate_search_results(collected)
        if deduplicated:
            return SearchAdapterResponse(results=deduplicated[:max_total_results])
        return SearchAdapterResponse(results=[], error=errors[0] if errors else None)


MockSearchAdapter = StaticSearchAdapter


def deduplicate_search_results(results: list[SearchResultSchema]) -> list[SearchResultSchema]:
    seen: set[str] = set()
    deduplicated: list[SearchResultSchema] = []
    for result in results:
        canonical_url = normalize_url(str(result.url))
        if canonical_url in seen:
            continue
        seen.add(canonical_url)
        deduplicated.append(result)
    return deduplicated


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    normalized_query = urlencode(query_pairs, doseq=True)
    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            normalized_query,
            "",
        )
    )


def _deduplicate_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated


def _default_static_results() -> list[SearchResultSchema]:
    return [
        SearchResultSchema(
            title="MiroThinker-1.7 - Hugging Face",
            url="https://huggingface.co/example/mirothinker-1.7",
            snippet=(
                "MiroThinker 1.7 model card is released with model files and weights. "
                "License Apache-2.0 allows commercial use. "
                "It is described as an open-weight model."
            ),
            published_at=None,
        ),
        SearchResultSchema(
            title="MiroThinker GitHub repository",
            url="https://github.com/example/mirothinker",
            snippet=(
                "The GitHub repository provides source code for MiroThinker. "
                "The training data is not disclosed."
            ),
            published_at=None,
        ),
    ]
