"""Factory for constructing the configured LLM provider, with lazy imports so
users only need the dependency for the provider they actually use."""
from __future__ import annotations

from course_upgrader.config import settings
from course_upgrader.llm.base import LLMProvider

_provider_cache: dict[str, LLMProvider] = {}


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Return a cached instance of the requested LLM provider.

    Falls back to `COURSE_UPGRADER_LLM_PROVIDER` (default: "anthropic") when
    no explicit name is given.
    """
    provider_name = (provider_name or settings.llm_provider or "anthropic").lower()

    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "anthropic":
        from course_upgrader.llm.anthropic_provider import AnthropicProvider

        provider: LLMProvider = AnthropicProvider()
    elif provider_name == "gemini":
        from course_upgrader.llm.gemini_provider import GeminiProvider

        provider = GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM provider '{provider_name}'. Supported: anthropic, gemini.")

    _provider_cache[provider_name] = provider
    return provider
