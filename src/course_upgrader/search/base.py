"""Abstract base class for web search providers.

Any provider (DuckDuckGo, Tavily, Brave Search, Google Custom Search, etc.)
must implement this single-method interface so `course_searcher.py` stays
provider-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    """Common interface all web search providers must implement."""

    name: str = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Run a web search query and return a list of results."""
        raise NotImplementedError
