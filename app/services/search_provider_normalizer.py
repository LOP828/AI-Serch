from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import ValidationError

from app.schemas.search import SearchResultSchema


def normalize_tavily_results(
    raw_payload: Mapping[str, Any],
    max_results: int | None = None,
) -> list[SearchResultSchema]:
    items = _list_from(raw_payload.get("results"))
    return _normalize_items(
        items=items,
        title_keys=("title",),
        url_keys=("url",),
        snippet_keys=("content", "snippet"),
        published_at_keys=("published_date", "published_at"),
        max_results=max_results,
    )


def normalize_brave_results(
    raw_payload: Mapping[str, Any],
    max_results: int | None = None,
) -> list[SearchResultSchema]:
    web_payload = raw_payload.get("web")
    if not isinstance(web_payload, Mapping):
        return []
    items = _list_from(web_payload.get("results"))
    return _normalize_items(
        items=items,
        title_keys=("title",),
        url_keys=("url",),
        snippet_keys=("description", "snippet"),
        published_at_keys=(),
        max_results=max_results,
    )


def normalize_serpapi_results(
    raw_payload: Mapping[str, Any],
    max_results: int | None = None,
) -> list[SearchResultSchema]:
    items = _list_from(raw_payload.get("organic_results"))
    return _normalize_items(
        items=items,
        title_keys=("title",),
        url_keys=("link", "url"),
        snippet_keys=("snippet",),
        published_at_keys=("date",),
        max_results=max_results,
    )


def _normalize_items(
    items: Sequence[Mapping[str, Any]],
    title_keys: tuple[str, ...],
    url_keys: tuple[str, ...],
    snippet_keys: tuple[str, ...],
    published_at_keys: tuple[str, ...],
    max_results: int | None,
) -> list[SearchResultSchema]:
    normalized: list[SearchResultSchema] = []
    seen_urls: set[str] = set()
    for item in items:
        title = _first_text(item, title_keys)
        url = _first_text(item, url_keys)
        if not title or not url:
            continue

        canonical_url = _normalize_url(url)
        if canonical_url in seen_urls:
            continue

        try:
            result = SearchResultSchema(
                title=title,
                url=url,
                snippet=_first_text(item, snippet_keys) or "",
                published_at=_first_text(item, published_at_keys),
            )
        except ValidationError:
            continue

        seen_urls.add(canonical_url)
        normalized.append(result)
        if max_results is not None and len(normalized) >= max_results:
            break
    return normalized


def _list_from(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _first_text(item: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_url(url: str) -> str:
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
