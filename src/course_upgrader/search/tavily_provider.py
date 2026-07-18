"""Tavily-backed search provider — robust search API suited for AI agents.

Required configuration: TAVILY_API_KEY environment variable.
"""
from __future__ import annotations

import logging
import requests

from course_upgrader.config import settings
from course_upgrader.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class TavilyProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.tavily_api_key
        if not self.api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Export it or add it to a .env file "
                "to use the Tavily search provider."
            )

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            }
            # Tavily is much better behaved with site operators, so we can use standard site: searches
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=settings.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            return [
                SearchResult(
                    title=(r.get("title") or "").strip(),
                    url=(r.get("url") or "").strip(),
                    snippet=(r.get("content") or "").strip(),
                )
                for r in results
                if r.get("url")
            ]
        except Exception as exc:
            raise RuntimeError(f"Tavily search failed for query '{query}': {exc}") from exc
