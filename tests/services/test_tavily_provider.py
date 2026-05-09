import json
from urllib import error as urllib_error

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


def test_tavily_provider_allow_network_true_without_api_key_does_not_call_network() -> None:
    provider = TavilyProvider(api_key="", allow_network=True, timeout_seconds=2.0)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED
    assert response.metadata.debug["network_enabled"] is True
    assert response.metadata.debug["timeout_seconds"] == 2.0
    assert response.metadata.debug["fake_client"] is True


def test_tavily_provider_allow_network_false_does_not_call_fake_client() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Should not be called",
                    "url": "https://example.com/should-not-call",
                    "content": "unused",
                }
            ]
        }
    )
    provider = TavilyProvider(allow_network=False, request_func=fake_client)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE
    assert fake_client.calls == []


def test_tavily_provider_stub_does_not_expose_api_key_in_debug() -> None:
    provider = TavilyProvider(api_key="", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED
    assert "api_key" not in response.metadata.debug
    assert "test-not-real" not in repr(response.metadata.debug)


def test_tavily_provider_fake_client_success_returns_normalized_results() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Tavily fake result",
                    "url": "https://example.com/tavily-fake",
                    "content": "Fake Tavily snippet.",
                    "published_date": "2026-05-09",
                    "score": 0.99,
                    "raw_content": "Provider-only raw text.",
                    "provider": "tavily",
                },
                {
                    "title": "Second Tavily fake result",
                    "url": "https://example.com/tavily-fake-2",
                    "content": "Second snippet.",
                },
            ]
        }
    )
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        timeout_seconds=2.5,
        request_func=fake_client,
    )

    response = provider.search("MiroThinker 1.7", max_results=1)

    assert response.error_code is None
    assert len(response.normalized_results) == 1
    result = response.normalized_results[0]
    assert isinstance(result, SearchResultSchema)
    assert result.title == "Tavily fake result"
    assert str(result.url) == "https://example.com/tavily-fake"
    assert result.snippet == "Fake Tavily snippet."
    assert result.published_at == "2026-05-09"
    assert response.metadata.provider == "tavily"
    assert response.metadata.debug["fake_client"] is True
    assert response.metadata.debug["network_enabled"] is True
    assert response.metadata.raw_payload is not None
    assert fake_client.calls == [
        {
            "url": "https://api.tavily.com/search",
            "headers": {
                "Authorization": "Bearer test-api-key",
                "Content-Type": "application/json",
            },
            "json": {
                "query": "MiroThinker 1.7",
                "max_results": 1,
            },
            "timeout_seconds": 2.5,
        }
    ]


def test_tavily_provider_fake_client_keeps_provider_fields_out_of_schema() -> None:
    fake_client = RecordingTavilyClient(
        payload={
            "results": [
                {
                    "title": "Provider fields",
                    "url": "https://example.com/provider-fields",
                    "content": "snippet",
                    "score": 0.77,
                    "raw_content": "raw",
                    "provider": "tavily",
                }
            ],
            "request_id": "fake-request",
        }
    )
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=fake_client,
    )

    response = provider.search("query", max_results=1)
    result_data = response.normalized_results[0].model_dump()

    assert set(result_data) == {"title", "url", "snippet", "published_at"}
    assert "score" not in result_data
    assert "raw_content" not in result_data
    assert "provider" not in result_data
    assert "request_id" not in result_data


def test_tavily_provider_fake_client_empty_results_are_valid() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"results": []}),
    )

    response = provider.search("query", max_results=3)

    assert response.normalized_results == []
    assert response.error_code is None


def test_tavily_provider_fake_client_timeout_maps_to_provider_timeout() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RaisingTavilyClient(TimeoutError("fake timeout")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_TIMEOUT
    assert response.metadata.debug["fake_client"] is True


def test_tavily_provider_fake_client_auth_failed_maps_to_provider_auth_failed() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RaisingTavilyClient(FakeHttpError(401, "unauthorized")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED


def test_tavily_provider_fake_client_forbidden_maps_to_provider_auth_failed() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RaisingTavilyClient(FakeHttpError(403, "forbidden")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED


def test_tavily_provider_fake_client_rate_limit_maps_to_provider_rate_limited() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"status_code": 429, "error": "rate limited"}),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_RATE_LIMITED


def test_tavily_provider_fake_client_quota_maps_to_provider_quota_exceeded() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(
            payload={"status_code": 429, "error": "quota exhausted"},
        ),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED


def test_tavily_provider_fake_client_bad_payload_maps_to_provider_bad_response() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"results": "not-a-list"}),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_BAD_RESPONSE


def test_tavily_provider_fake_client_5xx_maps_to_provider_unavailable() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(
            payload={"status_code": 503, "error": "service unavailable"},
        ),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


def test_tavily_provider_fake_client_generic_exception_maps_to_provider_unavailable() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RaisingTavilyClient(RuntimeError("fake network unavailable")),
    )

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


def test_tavily_provider_enabled_without_api_key_returns_auth_failed() -> None:
    fake_client = RecordingTavilyClient(payload={"results": []})
    provider = TavilyProvider(allow_network=True, request_func=fake_client)

    response = provider.search("query", max_results=1)

    assert response.normalized_results == []
    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED
    assert fake_client.calls == []
    assert "api_key" not in response.metadata.debug


def test_tavily_provider_request_metadata_does_not_expose_api_key() -> None:
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=RecordingTavilyClient(payload={"results": []}),
    )

    response = provider.search("query", max_results=1)

    assert response.error_code is None
    assert "api_key" not in response.metadata.debug
    assert "test-api-key" not in repr(response.metadata.debug)
    assert "test-api-key" not in repr(response.metadata.raw_payload)


def test_tavily_provider_uses_configured_base_url_for_search_endpoint() -> None:
    fake_client = RecordingTavilyClient(payload={"results": []})
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        request_func=fake_client,
        base_url="https://example.test/tavily/",
    )

    response = provider.search("query", max_results=4)

    assert response.error_code is None
    assert fake_client.calls[0]["url"] == "https://example.test/tavily/search"
    assert fake_client.calls[0]["json"] == {"query": "query", "max_results": 4}


def test_tavily_provider_default_client_builds_post_request(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_urlopen(request, timeout):
        calls.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "authorization": request.get_header("Authorization"),
                "content_type": request.get_header("Content-type"),
                "body": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return FakeUrlopenResponse(
            {
                "results": [
                    {
                        "title": "Default client result",
                        "url": "https://example.com/default-client",
                        "content": "Default client snippet.",
                    }
                ]
            }
        )

    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        fake_urlopen,
    )
    provider = TavilyProvider(
        api_key="test-api-key",
        allow_network=True,
        timeout_seconds=4.0,
    )

    response = provider.search("OpenAI", max_results=1)

    assert response.error_code is None
    assert response.normalized_results[0].title == "Default client result"
    assert calls == [
        {
            "url": "https://api.tavily.com/search",
            "method": "POST",
            "authorization": "Bearer test-api-key",
            "content_type": "application/json",
            "body": {"query": "OpenAI", "max_results": 1},
            "timeout": 4.0,
        }
    ]


def test_tavily_provider_default_client_maps_401_to_auth_failed(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(FakeUrlopenHttpError(401, "unauthorized")),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED


def test_tavily_provider_default_client_maps_403_to_auth_failed(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(FakeUrlopenHttpError(403, "forbidden")),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_AUTH_FAILED


def test_tavily_provider_default_client_maps_429_to_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(FakeUrlopenHttpError(429, "rate limited")),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_RATE_LIMITED


def test_tavily_provider_default_client_maps_quota_429_to_quota_exceeded(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(
            FakeUrlopenHttpError(429, "quota exhausted")
        ),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_QUOTA_EXCEEDED


def test_tavily_provider_default_client_maps_5xx_to_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(
            FakeUrlopenHttpError(503, "service unavailable")
        ),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


def test_tavily_provider_default_client_maps_socket_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(TimeoutError("timeout")),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_TIMEOUT


def test_tavily_provider_default_client_maps_bad_json_to_bad_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: FakeRawUrlopenResponse("not-json"),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_BAD_RESPONSE


def test_tavily_provider_default_client_maps_url_error_to_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(
            urllib_error.URLError("network unavailable")
        ),
    )
    provider = TavilyProvider(api_key="test-api-key", allow_network=True)

    response = provider.search("query", max_results=1)

    assert response.error_code == SearchProviderErrorCode.PROVIDER_UNAVAILABLE


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


class RecordingTavilyClient:
    def __init__(self, payload) -> None:
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
        timeout_seconds: float | None,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self._payload


class RaisingTavilyClient:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def __call__(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
        timeout_seconds: float | None,
    ):
        del url, headers, json, timeout_seconds
        raise self._exc


class FakeHttpError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class FakeUrlopenResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class FakeRawUrlopenResponse:
    def __init__(self, body: str) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback
        return False

    def read(self) -> bytes:
        return self._body.encode("utf-8")


class FakeUrlopenHttpError(urllib_error.HTTPError):
    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(
            url="https://api.tavily.com/search",
            code=status_code,
            msg=body,
            hdrs=None,
            fp=None,
        )
        self._body = body

    def read(self) -> bytes:
        return self._body.encode("utf-8")
