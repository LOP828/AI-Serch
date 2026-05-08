import pytest

from app.core.config import Settings
from app.schemas.search import SearchResultSchema
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


@pytest.mark.parametrize("provider_name", ["tavily", "brave", "serpapi"])
def test_real_provider_names_are_explicitly_not_implemented(provider_name: str) -> None:
    settings = Settings(_env_file=None, search_provider=provider_name)

    with pytest.raises(SearchProviderNotImplementedError, match=provider_name):
        build_search_adapter(settings)


def test_invalid_provider_name_has_clear_error() -> None:
    settings = Settings(_env_file=None, search_provider="unknown-provider")

    with pytest.raises(SearchProviderConfigurationError, match="unknown-provider"):
        build_search_adapter(settings)


def test_search_settings_do_not_define_api_key_field() -> None:
    settings = Settings(_env_file=None)

    assert settings.search_provider == "static"
    assert not hasattr(settings, "search_api_key")
