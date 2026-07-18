"""Factory for constructing the configured web search provider, with lazy imports."""
from __future__ import annotations

from course_upgrader.config import settings
from course_upgrader.search.base import SearchProvider

_provider_cache: dict[str, SearchProvider] = {}


def get_search_provider(provider_name: str | None = None) -> SearchProvider:
    """Return a cached instance of the requested search provider.

    Falls back to `COURSE_UPGRADER_SEARCH_PROVIDER` (default: "duckduckgo") when
    no explicit name is given.
    """
    provider_name = (provider_name or settings.search_provider or "duckduckgo").lower()

    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "duckduckgo":
        from course_upgrader.search.duckduckgo_provider import DuckDuckGoProvider

        provider: SearchProvider = DuckDuckGoProvider()
    elif provider_name == "tavily":
        from course_upgrader.search.tavily_provider import TavilyProvider

        provider = TavilyProvider()
    else:
        raise ValueError(f"Unknown search provider '{provider_name}'. Supported: duckduckgo, tavily.")

    _provider_cache[provider_name] = provider
    return provider
