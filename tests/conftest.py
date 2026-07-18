"""Shared pytest fixtures: fake LLM and search providers for offline testing."""
from __future__ import annotations

import pytest

from course_upgrader.llm.base import LLMProvider
from course_upgrader.search.base import SearchProvider, SearchResult


class FakeLLMProvider(LLMProvider):
    """Returns canned responses in order, without hitting any real API."""

    name = "fake"

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._call_count = 0
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        self.calls.append((system_prompt, user_prompt))
        if self._responses:
            response = self._responses[min(self._call_count, len(self._responses) - 1)]
            self._call_count += 1
            return response
        return "{}"


class FakeSearchProvider(SearchProvider):
    """Returns a canned list of SearchResult objects, without hitting the network."""

    name = "fake"

    def __init__(self, results: list[SearchResult] | None = None):
        self._results = results or []

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return self._results[:max_results]


@pytest.fixture
def fake_llm():
    return FakeLLMProvider


@pytest.fixture
def fake_search():
    return FakeSearchProvider
