"""Targeted course discovery across major e-learning platforms via web search."""
from __future__ import annotations

import logging

from course_upgrader.config import PLATFORM_DOMAINS, settings
from course_upgrader.models import CandidateProfile, Course, Platform
from course_upgrader.search.base import SearchProvider

logger = logging.getLogger(__name__)

FREE_HINTS = ("free", "audit", "no cost", "google digital garage")
PAID_HINTS = ("certificate", "specialization", "paid", "nanodegree", "professional certificate")


def build_search_queries(
    career_goal: str, platforms: list[str] | None = None, is_ddg: bool = False
) -> dict[str, str]:
    """Build one site-scoped search query per target platform."""
    platforms = platforms or list(PLATFORM_DOMAINS.keys())
    queries: dict[str, str] = {}
    for platform in platforms:
        domain = PLATFORM_DOMAINS.get(platform)
        if not domain:
            continue
        if is_ddg:
            # Strip site: and quotes to avoid DDG rate limiting and operator parsing bugs.
            # We use the platform name as a keyword, e.g. 'coursera AI Product Manager course'
            queries[platform] = f"{platform} {career_goal} course"
        else:
            # Standard search APIs like Tavily understand site: and quotes perfectly.
            queries[platform] = f'site:{domain} "{career_goal}" course'
    return queries


def infer_platform(url: str) -> Platform:
    """Infer the Platform enum value from a course URL's domain."""
    for platform_name, domain in PLATFORM_DOMAINS.items():
        if domain in url:
            return Platform(platform_name)
    return Platform.OTHER


def infer_price(title: str, snippet: str) -> str | None:
    """Best-effort guess at whether a course is free or paid from its title/snippet."""
    text = f"{title} {snippet}".lower()
    if any(hint in text for hint in FREE_HINTS):
        return "free"
    if any(hint in text for hint in PAID_HINTS):
        return "paid"
    return None


def fetch_page_text(url: str, timeout: int | None = None, max_chars: int = 4000) -> str:
    """Best-effort fetch of a course page's visible text, used for single-course checks.

    Returns an empty string on any failure (missing deps, network error, bad status)
    so callers can fall back gracefully instead of crashing.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.debug("requests/beautifulsoup4 not installed; skipping page fetch for %s", url)
        return ""

    try:
        response = requests.get(
            url,
            timeout=timeout or settings.request_timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CourseUpgraderBot/0.1)"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return text[:max_chars]
    except Exception as exc:  # noqa: BLE001 - any fetch/parse failure should degrade gracefully
        logger.debug("Failed to fetch page text from %s: %s", url, exc)
        return ""


def search_courses(
    profile: CandidateProfile,
    search_provider: SearchProvider,
    platforms: list[str] | None = None,
    max_results_per_platform: int | None = None,
) -> list[Course]:
    """Search each target platform for courses relevant to the candidate's career goal."""
    if not profile.career_goal:
        raise ValueError("CandidateProfile.career_goal is required to search for courses.")

    max_results = max_results_per_platform or settings.max_courses_per_platform
    is_ddg = getattr(search_provider, "name", "base") == "duckduckgo"
    queries = build_search_queries(profile.career_goal, platforms, is_ddg=is_ddg)

    courses: list[Course] = []
    seen_urls: set[str] = set()

    for platform_name, query in queries.items():
        try:
            results = search_provider.search(query, max_results=max_results)
        except Exception as exc:  # noqa: BLE001 - degrade gracefully per platform
            logger.warning("Search failed for platform '%s': %s", platform_name, exc)
            continue

        for result in results:
            if not result.url or result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            courses.append(
                Course(
                    title=result.title or "Untitled course",
                    url=result.url,
                    platform=infer_platform(result.url),
                    description=result.snippet,
                    price=infer_price(result.title, result.snippet),
                )
            )

    return courses
