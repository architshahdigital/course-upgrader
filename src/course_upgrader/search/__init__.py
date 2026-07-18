from course_upgrader.search.base import SearchProvider, SearchResult
from course_upgrader.search.duckduckgo_provider import DuckDuckGoProvider
from course_upgrader.search.tavily_provider import TavilyProvider
from course_upgrader.search.factory import get_search_provider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "DuckDuckGoProvider",
    "TavilyProvider",
    "get_search_provider",
]
