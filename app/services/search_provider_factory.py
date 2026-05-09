from collections.abc import Mapping

from app.core.config import Settings, get_settings
from app.services.providers.tavily_provider import TavilyProvider
from app.services.search_adapter import StaticSearchAdapter
from app.services.search_provider import FakeSearchProvider, SearchProvider

STATIC_PROVIDER_NAMES = frozenset({"static", "mock"})
RESERVED_PROVIDER_NAMES = frozenset({"brave", "serpapi"})


class SearchProviderConfigurationError(ValueError):
    """Raised when the configured search provider name is invalid."""


class SearchProviderNotImplementedError(NotImplementedError):
    """Raised when a real provider name is configured before implementation exists."""


def build_search_adapter(
    settings: Settings | None = None,
    provider_overrides: Mapping[str, SearchProvider] | None = None,
) -> StaticSearchAdapter:
    resolved_settings = settings or get_settings()
    provider_name = resolved_settings.search_provider.strip().lower()

    if provider_name in STATIC_PROVIDER_NAMES:
        return StaticSearchAdapter()

    if provider_name == "fake":
        provider = (provider_overrides or {}).get("fake", FakeSearchProvider())
        return StaticSearchAdapter(provider=provider)

    if provider_name == "tavily":
        return StaticSearchAdapter(
            provider=TavilyProvider(
                timeout_seconds=resolved_settings.search_timeout_seconds,
                allow_network=False,
            )
        )

    if provider_name in RESERVED_PROVIDER_NAMES:
        raise SearchProviderNotImplementedError(
            f"Search provider '{provider_name}' is reserved but not implemented."
        )

    raise SearchProviderConfigurationError(
        f"Unsupported search provider '{resolved_settings.search_provider}'."
    )
