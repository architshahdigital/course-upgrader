"""Abstract base class for LLM providers.

Any provider (Anthropic, Gemini, or a future one) must implement this
single-method interface so the rest of the engine stays provider-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common interface all LLM providers must implement."""

    name: str = "base"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        """Send a system + user prompt to the LLM and return the raw text response."""
        raise NotImplementedError
