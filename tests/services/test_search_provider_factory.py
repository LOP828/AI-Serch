import pytest

from app.core.config import Settings
from app.schemas.search import SearchResultSchema
from app.services.providers.tavily_provider import TavilyProvider
from app.services.search_provider import FakeSearchProvider
from app.services.search_provider_factory import (
    SearchProviderConfigurationError,
    SearchProviderNotImplementedError,
    build_search_adapter,
)


def test_default_settings_build_static_search_adapter_behavior() -> None:
    adapter = build_search_adapter(Settings(_env_file=None))

    response = adapter.search("MiroThinker 1.7", max_results=1)

    assert response.error is None
    assert len(response.results) == 1
    assert response.results[0].title == "MiroThinker-1.7 - Hugging Face"


@pytest.mark.parametrize("provider_name", ["static", "mock", "STATIC", " Mock "])
def test_static_and_mock_provider_names_keep_static_behavior(provider_name: str) -> None:
    settings = Settings(_env_file=None, search_provider=provider_name)

    response = build_search_adapter(settings).search("query", max_results=2)

    assert response.error is None
    assert [result.title for result in response.results] == [
        "MiroThinker-1.7 - Hugging Face",
        "MiroThinker GitHub repository",
    ]


def test_fake_provider_can_be_injected_by_factory_for_tests() -> None:
    provider = FakeSearchProvider(
        results=[
            SearchResultSchema(
                title="Injected fake result",
                url="https://example.com/injected-fake",
                snippet="factory fake snippet",
            )
        ]
    )
    settings = Settings(_env_file=None, search_provider="fake")

    response = build_search_adapter(
        settings,
        provider_overrides={"fake": provider},
    ).search("factory query", max_results=1)

    assert response.error is None
    assert [result.title for result in response.results] == ["Injected fake result"]
    assert provider.queries == ["factory query"]
    assert provider.max_results_values == [1]


def test_fake_provider_default_is_non_network_test_provider() -> None:
    settings = Settings(_env_file=None, search_provider="fake")

    response = build_search_adapter(settings).search("query", max_results=1)

    assert response.error is None
    assert response.results[0].title == "Fake provider model card"


def test_static_provider_ignores_fake_override_and_keeps_static_path() -> None:
    settings = Settings(_env_file=None, search_provider="static")
    provider = FakeSearchProvider(
        results=[
            SearchResultSchema(
                title="Should not be used",
                url="https://example.com/not-used",
                snippet="not used",
            )
        ]
    )

    response = build_search_adapter(
        settings,
        provider_overrides={"fake": provider},
    ).search("query", max_results=1)

    assert response.error is None
    assert response.results[0].title == "MiroThinker-1.7 - Hugging Face"
    assert provider.queries == []


def test_tavily_provider_builds_disabled_opt_in_adapter() -> None:
    settings = Settings(_env_file=None, search_provider="tavily")

    adapter = build_search_adapter(settings)
    response = adapter.search("query", max_results=2)

    assert isinstance(adapter._provider, TavilyProvider)
    assert adapter._provider._allow_network is False
    assert adapter._provider._request_func is None
    assert adapter._provider._api_key is None
    assert response.results == []
    assert response.error == "provider_unavailable"


def test_tavily_provider_opt_in_uses_configured_timeout_without_api_key() -> None:
    settings = Settings(
        _env_file=None,
        search_provider="tavily",
        search_timeout_seconds=3.5,
    )

    adapter = build_search_adapter(settings)
    provider_response = adapter._provider.search("query", max_results=1)

    assert isinstance(adapter._provider, TavilyProvider)
    assert provider_response.metadata.debug["network_enabled"] is False
    assert provider_response.metadata.debug["timeout_seconds"] == 3.5
    assert "api_key" not in provider_response.metadata.debug


@pytest.mark.parametrize("provider_name", ["brave", "serpapi"])
def test_real_provider_names_are_explicitly_not_implemented(provider_name: str) -> None:
    settings = Settings(_env_file=None, search_provider=provider_name)

    with pytest.raises(SearchProviderNotImplementedError, match=provider_name):
        build_search_adapter(settings)


@pytest.mark.parametrize("provider_name", ["brave", "serpapi"])
def test_real_provider_names_cannot_be_enabled_by_test_override(provider_name: str) -> None:
    settings = Settings(_env_file=None, search_provider=provider_name)
    provider = FakeSearchProvider()

    with pytest.raises(SearchProviderNotImplementedError, match=provider_name):
        build_search_adapter(settings, provider_overrides={provider_name: provider})

    assert provider.queries == []


def test_tavily_provider_override_does_not_enable_network_path() -> None:
    settings = Settings(_env_file=None, search_provider="tavily")
    provider = FakeSearchProvider()

    response = build_search_adapter(settings, provider_overrides={"tavily": provider}).search(
        "query",
        max_results=1,
    )

    assert response.results == []
    assert response.error == "provider_unavailable"
    assert provider.queries == []


def test_invalid_provider_name_has_clear_error() -> None:
    settings = Settings(_env_file=None, search_provider="unknown-provider")

    with pytest.raises(SearchProviderConfigurationError, match="unknown-provider"):
        build_search_adapter(settings)


def test_search_settings_do_not_define_api_key_field() -> None:
    settings = Settings(_env_file=None)

    assert settings.search_provider == "static"
    assert not hasattr(settings, "search_api_key")
