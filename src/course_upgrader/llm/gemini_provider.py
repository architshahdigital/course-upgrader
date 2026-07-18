"""Google Gemini LLM provider (alternative provider for the Course Upgrader agent)."""
from __future__ import annotations

from course_upgrader.config import settings
from course_upgrader.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "The 'google-genai' package is required for the Gemini provider. "
                "Install it with: pip install google-genai"
            ) from exc

        api_key = api_key or settings.gemini_api_key
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Export it or add it to a .env file "
                "(see .env.example)."
            )

        self.model = model or settings.gemini_model
        self._client = genai.Client(api_key=api_key)

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text or ""
