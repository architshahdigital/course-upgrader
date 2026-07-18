"""DuckDuckGo-backed search provider — free, no API key required.

Used to run `site:<domain>` scoped queries against each target e-learning
platform (Coursera, Udemy, edX, Simplilearn, Great Learning, Google Digital
Garage).
"""
from __future__ import annotations

import logging
import time

from course_upgrader.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def __init__(self, region: str = "wt-wt", max_retries: int = 3, retry_delay: float = 2.0):
        self.region = region
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            from duckduckgo_search import DDGS
        except ImportError as exc:
            raise RuntimeError(
                "The 'duckduckgo_search' package is required. "
                "Install it with: pip install duckduckgo_search"
            ) from exc

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, region=self.region, max_results=max_results))
                return [
                    SearchResult(
                        title=(r.get("title") or "").strip(),
                        url=(r.get("href") or "").strip(),
                        snippet=(r.get("body") or "").strip(),
                    )
                    for r in raw_results
                    if r.get("href")
                ]
            except Exception as exc:  # noqa: BLE001 - underlying network/library errors vary
                last_error = exc
                logger.debug("DuckDuckGo search attempt %d/%d failed: %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(f"DuckDuckGo search failed after {self.max_retries} attempts: {last_error}")
