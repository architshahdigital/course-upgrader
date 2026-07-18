"""Anthropic Claude LLM provider (default provider for the Course Upgrader skill)."""
from __future__ import annotations

from course_upgrader.config import settings
from course_upgrader.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The 'anthropic' package is required for the Anthropic provider. "
                "Install it with: pip install anthropic"
            ) from exc

        api_key = api_key or settings.anthropic_api_key
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or add it to a .env file "
                "(see .env.example)."
            )

        self.model = model or settings.anthropic_model
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
