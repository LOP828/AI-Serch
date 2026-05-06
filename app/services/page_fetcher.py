import re
from datetime import UTC, datetime
from html.parser import HTMLParser

import httpx

from app.schemas.page import PageFetchResultSchema
from app.schemas.source import FetchStatus, SourceSchema

DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_TEXT_LENGTH = 20_000
USER_AGENT = "CriticalSearchLayer/0.1"


class PageFetcher:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_text_length: int = DEFAULT_MAX_TEXT_LENGTH,
    ) -> None:
        self._http_client = http_client
        self._timeout_seconds = timeout_seconds
        self._max_text_length = max_text_length

    def fetch_source(self, source: SourceSchema) -> PageFetchResultSchema:
        return self.fetch(url=str(source.url), title=source.title, snippet=source.snippet)

    def fetch(
        self,
        url: str,
        title: str | None = None,
        snippet: str | None = None,
    ) -> PageFetchResultSchema:
        fetched_at = _utc_now()
        try:
            html = self._get_url(url)
            text, extracted_title = extract_text_from_html(html)
            text = _limit_text(text, self._max_text_length)
            if text:
                return PageFetchResultSchema(
                    url=url,
                    title=extracted_title or title,
                    text=text,
                    fetch_status=FetchStatus.SUCCESS,
                    fetched_at=fetched_at,
                )
            return self._fallback(url, title, snippet, fetched_at, "empty extracted text")
        except httpx.TimeoutException as exc:
            return self._fallback(url, title, snippet, fetched_at, f"timeout: {exc}")
        except httpx.HTTPStatusError as exc:
            return self._fallback(
                url,
                title,
                snippet,
                fetched_at,
                f"http error: {exc.response.status_code}",
            )
        except httpx.HTTPError as exc:
            return self._fallback(url, title, snippet, fetched_at, f"network error: {exc}")

    def _get_url(self, url: str) -> str:
        headers = {"User-Agent": USER_AGENT}
        if self._http_client:
            response = self._http_client.get(url, headers=headers, timeout=self._timeout_seconds)
        else:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=self._timeout_seconds)
        response.raise_for_status()
        return response.text

    def _fallback(
        self,
        url: str,
        title: str | None,
        snippet: str | None,
        fetched_at: str,
        error_message: str,
    ) -> PageFetchResultSchema:
        fallback_text = _limit_text(_normalize_whitespace(snippet or ""), self._max_text_length)
        return PageFetchResultSchema(
            url=url,
            title=title,
            text=fallback_text,
            fetch_status=FetchStatus.FALLBACK if fallback_text else FetchStatus.FAILED,
            error_message=error_message,
            fetched_at=fetched_at,
        )


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self._in_title = False
        self._ignored_depth = 0
        self._text_chunks: list[str] = []
        self._title_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        if normalized_tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        if normalized_tag == "title":
            self._in_title = False
            title = _normalize_whitespace(" ".join(self._title_chunks))
            self.title = title or None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self._title_chunks.append(data)
            return
        self._text_chunks.append(data)

    @property
    def text(self) -> str:
        return _normalize_whitespace(" ".join(self._text_chunks))


def extract_text_from_html(html: str) -> tuple[str, str | None]:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text, parser.title


def build_fallback_http_client(error_message: str = "stage 5 mock fetch disabled") -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(error_message, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _limit_text(text: str, max_text_length: int) -> str:
    if len(text) <= max_text_length:
        return text
    return text[:max_text_length].rstrip()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
