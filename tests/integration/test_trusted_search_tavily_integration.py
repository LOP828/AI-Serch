import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.trusted_search import TrustedSearchResponse

RUN_INTEGRATION_ENV = "CSL_RUN_INTEGRATION_TESTS"
PROVIDER_ENV = "CSL_SEARCH_PROVIDER"
API_KEY_ENV = "CSL_SEARCH_API_KEY"
ALLOW_NETWORK_ENV = "CSL_SEARCH_ALLOW_NETWORK"

client = TestClient(app)


def get_trusted_search_tavily_skip_reason(env: dict[str, str] | None = None) -> str | None:
    values = env if env is not None else os.environ
    if values.get(RUN_INTEGRATION_ENV, "").lower() != "true":
        return f"{RUN_INTEGRATION_ENV}=true is required for Tavily route integration tests."
    if values.get(PROVIDER_ENV, "").strip().lower() != "tavily":
        return f"{PROVIDER_ENV}=tavily is required for Tavily route integration tests."
    if values.get(ALLOW_NETWORK_ENV, "").lower() != "true":
        return f"{ALLOW_NETWORK_ENV}=true is required for Tavily route integration tests."
    if not values.get(API_KEY_ENV, "").strip():
        return f"{API_KEY_ENV} is required for Tavily route integration tests."
    return None


def test_trusted_search_tavily_route_integration_gate_skips_when_not_opted_in() -> None:
    reason = get_trusted_search_tavily_skip_reason({})

    assert reason == f"{RUN_INTEGRATION_ENV}=true is required for Tavily route integration tests."


def test_trusted_search_tavily_route_integration_gate_requires_tavily_provider() -> None:
    reason = get_trusted_search_tavily_skip_reason(
        {
            RUN_INTEGRATION_ENV: "true",
            PROVIDER_ENV: "static",
            ALLOW_NETWORK_ENV: "true",
            API_KEY_ENV: "temporary-test-key",
        }
    )

    assert reason == f"{PROVIDER_ENV}=tavily is required for Tavily route integration tests."


def test_trusted_search_tavily_route_integration_gate_requires_allow_network() -> None:
    reason = get_trusted_search_tavily_skip_reason(
        {
            RUN_INTEGRATION_ENV: "true",
            PROVIDER_ENV: "tavily",
            API_KEY_ENV: "temporary-test-key",
        }
    )

    assert reason == f"{ALLOW_NETWORK_ENV}=true is required for Tavily route integration tests."


def test_trusted_search_tavily_route_integration_gate_requires_api_key() -> None:
    reason = get_trusted_search_tavily_skip_reason(
        {
            RUN_INTEGRATION_ENV: "true",
            PROVIDER_ENV: "tavily",
            ALLOW_NETWORK_ENV: "true",
        }
    )

    assert reason == f"{API_KEY_ENV} is required for Tavily route integration tests."


@pytest.mark.integration
def test_trusted_search_route_can_use_tavily_provider_opt_in() -> None:
    skip_reason = get_trusted_search_tavily_skip_reason()
    if skip_reason is not None:
        pytest.skip(skip_reason)

    get_settings.cache_clear()
    try:
        response = client.post(
            "/api/v1/trusted-search",
            json={"query": "OpenAI official blog", "max_sources": 2},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    parsed = TrustedSearchResponse.model_validate(body)
    assert parsed.query == "OpenAI official blog"
    assert parsed.claims
    assert len(parsed.sources) <= 2
    assert parsed.answer_constraints
    assert isinstance(body["claims"], list)
    assert isinstance(body["sources"], list)
    assert isinstance(body["answer_constraints"], dict)
    assert all(isinstance(claim["evidence"], list) for claim in body["claims"])
    assert os.environ[API_KEY_ENV] not in response.text
    assert "api_key" not in response.text.lower()
    assert "authorization" not in response.text.lower()
