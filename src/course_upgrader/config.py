"""Runtime configuration for Course Upgrader, loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Platforms targeted by the course searcher, mapped to their search-engine domain.
PLATFORM_DOMAINS: dict[str, str] = {
    "coursera": "coursera.org",
    "udemy": "udemy.com",
    "edx": "edx.org",
    "simplilearn": "simplilearn.com",
    "great_learning": "mygreatlearning.com",
    "google_digital_garage": "learndigital.withgoogle.com",
}


@dataclass
class Settings:
    llm_provider: str = field(default_factory=lambda: os.getenv("COURSE_UPGRADER_LLM_PROVIDER", "anthropic"))
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    gemini_api_key: str | None = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL))
    search_provider: str = field(default_factory=lambda: os.getenv("COURSE_UPGRADER_SEARCH_PROVIDER", "duckduckgo"))
    tavily_api_key: str | None = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    max_courses_per_platform: int = field(
        default_factory=lambda: int(os.getenv("COURSE_UPGRADER_MAX_PER_PLATFORM", "5"))
    )
    request_timeout: int = field(default_factory=lambda: int(os.getenv("COURSE_UPGRADER_TIMEOUT", "15")))


settings = Settings()
