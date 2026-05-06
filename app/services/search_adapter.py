from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.schemas.search import SearchResultSchema


@dataclass(frozen=True)
class SearchAdapterResponse:
    results: list[SearchResultSchema]
    error: str | None = None


class SearchAdapter(Protocol):
    def search(self, query: str, max_results: int = 8) -> SearchAdapterResponse:
        """Return normalized search results without raising provider errors."""


class StaticSearchAdapter:
    def __init__(
        self,
        results: list[SearchResultSchema] | None = None,
        should_fail: bool = False,
    ) -> None:
        self._results = results or _default_static_results()
        self._should_fail = should_fail

    def search(self, query: str, max_results: int = 8) -> SearchAdapterResponse:
        if self._should_fail:
            return SearchAdapterResponse(results=[], error="mock_search_failure")

        del query
        deduplicated = deduplicate_search_results(self._results)
        return SearchAdapterResponse(results=deduplicated[:max_results])


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


def _default_static_results() -> list[SearchResultSchema]:
    return [
        SearchResultSchema(
            title="MiroThinker-1.7 - Hugging Face",
            url="https://huggingface.co/example/mirothinker-1.7",
            snippet="Mock model card result for MiroThinker 1.7.",
            published_at=None,
        ),
        SearchResultSchema(
            title="MiroThinker GitHub repository",
            url="https://github.com/example/mirothinker",
            snippet="Mock source repository result for MiroThinker.",
            published_at=None,
        ),
    ]
