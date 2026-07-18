"""Core data models for the Course Upgrader engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    HIGHLY_RECOMMENDED = "highly_recommended"
    RECOMMENDED = "recommended"
    PARTIAL_OVERLAP = "partial_overlap"
    REDUNDANT = "redundant"


class Platform(str, Enum):
    COURSERA = "coursera"
    UDEMY = "udemy"
    EDX = "edx"
    SIMPLILEARN = "simplilearn"
    GREAT_LEARNING = "great_learning"
    GOOGLE_DIGITAL_GARAGE = "google_digital_garage"
    OTHER = "other"


@dataclass
class CandidateProfile:
    """Structured profile extracted from a candidate's resume."""

    name: str | None
    raw_text: str
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    job_titles: list[str] = field(default_factory=list)
    experience_years: float | None = None
    education: list[str] = field(default_factory=list)
    career_goal: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "tools": self.tools,
            "job_titles": self.job_titles,
            "experience_years": self.experience_years,
            "education": self.education,
            "career_goal": self.career_goal,
        }


@dataclass
class Course:
    """A course discovered via web search on one of the target platforms."""

    title: str
    url: str
    platform: Platform
    description: str = ""
    price: str | None = None  # "free" | "paid" | None (unknown)
    provider: str | None = None  # e.g. "IBM", "Google", "University of Michigan"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "platform": self.platform.value,
            "description": self.description,
            "price": self.price,
            "provider": self.provider,
        }


@dataclass
class CourseAnalysis:
    """Result of running the semantic overlap engine on a single course."""

    course: Course
    overlap_rate: float  # 0-100, % of course the candidate already knows
    skill_delta: list[str]  # new tools/concepts/frameworks gained
    match_score: float  # 0-100, personalized value-for-time/money score
    verdict: Verdict
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "course": self.course.to_dict(),
            "overlap_rate": self.overlap_rate,
            "skill_delta": self.skill_delta,
            "match_score": self.match_score,
            "verdict": self.verdict.value,
            "reasoning": self.reasoning,
        }
