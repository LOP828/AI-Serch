import httpx

from app.schemas.source import FetchStatus
from app.services.page_fetcher import PageFetcher


def test_fetcher_extracts_text_from_successful_html() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            text="""
            <html>
              <head><title>Example Page</title><style>.hidden { color: red; }</style></head>
              <body><script>ignored()</script><main>Hello   world from HTML.</main></body>
            </html>
            """,
        )

    fetcher = PageFetcher(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = fetcher.fetch("https://example.com/page", snippet="fallback snippet")

    assert result.fetch_status == FetchStatus.SUCCESS
    assert result.title == "Example Page"
    assert result.text == "Hello world from HTML."
    assert result.error_message is None


def test_fetcher_uses_snippet_fallback_on_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    fetcher = PageFetcher(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = fetcher.fetch(
        "https://example.com/timeout",
        title="Timeout Page",
        snippet="Snippet fallback text.",
    )

    assert result.fetch_status == FetchStatus.FALLBACK
    assert result.title == "Timeout Page"
    assert result.text == "Snippet fallback text."
    assert result.error_message
    assert "timeout" in result.error_message


def test_fetcher_uses_snippet_fallback_on_empty_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text="<html><body>   </body></html>")

    fetcher = PageFetcher(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = fetcher.fetch("https://example.com/empty", snippet="Search snippet.")

    assert result.fetch_status == FetchStatus.FALLBACK
    assert result.text == "Search snippet."
    assert result.error_message == "empty extracted text"


def test_fetcher_limits_text_length() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text=f"<html><body>{'a' * 100}</body></html>")

    fetcher = PageFetcher(
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_text_length=12,
    )

    result = fetcher.fetch("https://example.com/long")

    assert result.fetch_status == FetchStatus.SUCCESS
    assert result.text == "a" * 12
