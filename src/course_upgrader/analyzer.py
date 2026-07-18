"""Semantic overlap engine: compares courses against a candidate profile using
an LLM to compute overlap rate, skill delta, and a personalized match score."""
from __future__ import annotations

import logging

from course_upgrader.llm.base import LLMProvider
from course_upgrader.models import CandidateProfile, Course, CourseAnalysis, Verdict
from course_upgrader.utils import extract_json, truncate

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are an expert career coach and curriculum analyst.
You compare a course's syllabus/description against a candidate's existing skills
and career goal to determine how much genuinely NEW value the course offers.

Respond with ONLY valid JSON (no markdown fences, no commentary) matching this schema:
{
  "overlap_rate": number,       // 0-100, percentage of course content the candidate already knows
  "skill_delta": string[],      // specific new tools, libraries, concepts, or frameworks gained
  "match_score": number,        // 0-100, personalized value-for-time/money score
  "verdict": "highly_recommended" | "recommended" | "partial_overlap" | "redundant",
  "reasoning": string            // 1-3 sentence justification
}

Scoring guidance:
- overlap_rate near 100 means the course teaches almost nothing the candidate doesn't
  already know (mark as "redundant").
- match_score should weigh both the size of the skill delta AND its relevance to the
  candidate's stated career goal. A course with a small but highly relevant delta can
  outscore one with a large but irrelevant delta.
- verdict thresholds (guideline, use judgment): match_score >= 75 -> highly_recommended,
  50-74 -> recommended, 25-49 -> partial_overlap, <25 or overlap_rate >= 85 -> redundant."""


def _build_user_prompt(profile: CandidateProfile, course: Course) -> str:
    return f"""CANDIDATE PROFILE
Name: {profile.name or "N/A"}
Career goal: {profile.career_goal or "N/A"}
Experience: {profile.experience_years if profile.experience_years is not None else "unknown"} years
Job titles: {", ".join(profile.job_titles) or "N/A"}
Existing skills: {", ".join(profile.skills) or "N/A"}
Existing tools/frameworks: {", ".join(profile.tools) or "N/A"}
Education: {", ".join(profile.education) or "N/A"}

COURSE
Title: {course.title}
Platform: {course.platform.value}
URL: {course.url}
Description/snippet: {truncate(course.description, 2000) or "N/A"}

Analyze this course against the candidate profile and return the JSON result."""


def analyze_course(profile: CandidateProfile, course: Course, llm: LLMProvider) -> CourseAnalysis:
    """Run the semantic overlap engine for a single course."""
    response = llm.complete(
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=_build_user_prompt(profile, course),
        max_tokens=800,
    )

    try:
        data = extract_json(response)
    except Exception as exc:
        logger.warning("Failed to parse LLM analysis for '%s': %s", course.title, exc)
        return CourseAnalysis(
            course=course,
            overlap_rate=50.0,
            skill_delta=[],
            match_score=0.0,
            verdict=Verdict.PARTIAL_OVERLAP,
            reasoning="Analysis unavailable due to a parsing error.",
        )

    verdict_raw = str(data.get("verdict", "partial_overlap")).lower()
    try:
        verdict = Verdict(verdict_raw)
    except ValueError:
        verdict = Verdict.PARTIAL_OVERLAP

    return CourseAnalysis(
        course=course,
        overlap_rate=float(data.get("overlap_rate", 50)),
        skill_delta=list(data.get("skill_delta") or []),
        match_score=float(data.get("match_score", 0)),
        verdict=verdict,
        reasoning=str(data.get("reasoning", "")),
    )


def analyze_courses(profile: CandidateProfile, courses: list[Course], llm: LLMProvider) -> list[CourseAnalysis]:
    """Run the semantic overlap engine across all discovered courses, ranked
    by match_score descending."""
    results: list[CourseAnalysis] = []
    for course in courses:
        try:
            results.append(analyze_course(profile, course, llm))
        except Exception as exc:  # noqa: BLE001 - keep going on a single course failure
            logger.warning("Skipping course '%s' due to error: %s", course.title, exc)

    return sorted(results, key=lambda r: r.match_score, reverse=True)
