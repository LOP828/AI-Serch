import os

import pytest

from app.services.providers.tavily_provider import TavilyProvider

RUN_INTEGRATION_ENV = "CSL_RUN_INTEGRATION_TESTS"
API_KEY_ENV = "CSL_SEARCH_API_KEY"
ALLOW_NETWORK_ENV = "CSL_SEARCH_ALLOW_NETWORK"


def should_run_integration_tests(env: dict[str, str] | None = None) -> bool:
    values = env if env is not None else os.environ
    return values.get(RUN_INTEGRATION_ENV, "").lower() == "true"


def get_tavily_skip_reason(env: dict[str, str] | None = None) -> str | None:
    values = env if env is not None else os.environ
    if not should_run_integration_tests(values):
        return f"{RUN_INTEGRATION_ENV}=true is required for Tavily integration tests."
    if not values.get(API_KEY_ENV, "").strip():
        return f"{API_KEY_ENV} is required for Tavily integration tests."
    if values.get(ALLOW_NETWORK_ENV, "").lower() != "true":
        return f"{ALLOW_NETWORK_ENV}=true is required for Tavily integration tests."
    return None


def test_integration_gate_skips_when_not_opted_in() -> None:
    reason = get_tavily_skip_reason({})

    assert reason == f"{RUN_INTEGRATION_ENV}=true is required for Tavily integration tests."


def test_integration_gate_skips_without_api_key() -> None:
    reason = get_tavily_skip_reason(
        {
            RUN_INTEGRATION_ENV: "true",
            ALLOW_NETWORK_ENV: "true",
        }
    )

    assert reason == f"{API_KEY_ENV} is required for Tavily integration tests."


def test_integration_gate_skips_without_allow_network() -> None:
    reason = get_tavily_skip_reason(
        {
            RUN_INTEGRATION_ENV: "true",
            API_KEY_ENV: "test-api-key",
        }
    )

    assert reason == f"{ALLOW_NETWORK_ENV}=true is required for Tavily integration tests."


@pytest.mark.integration
def test_tavily_provider_real_network_integration_placeholder() -> None:
    skip_reason = get_tavily_skip_reason()
    if skip_reason is not None:
        pytest.skip(skip_reason)

    provider = TavilyProvider(
        api_key=os.environ[API_KEY_ENV],
        allow_network=True,
        request_func=None,
    )
    response = provider.search("MiroThinker 1.7", max_results=1)

    assert response.normalized_results == []
    assert response.error_code is not None
    assert response.error_code.value == "provider_unavailable"
    assert response.metadata.debug["reason"] == (
        "No request function is configured; real network access is not enabled."
    )
    pytest.skip("Real Tavily HTTP client is not implemented yet.")
