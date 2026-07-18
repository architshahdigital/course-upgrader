"""Tests for analyzer.py"""
from __future__ import annotations

import json

from course_upgrader.analyzer import analyze_course, analyze_courses
from course_upgrader.models import CandidateProfile, Course, Platform, Verdict

PROFILE = CandidateProfile(
    name="Jane Doe",
    raw_text="...",
    skills=["Python", "SQL"],
    tools=["pandas", "numpy"],
    career_goal="Machine Learning Engineer",
)

COURSE = Course(
    title="Intro to Machine Learning with TensorFlow",
    url="https://coursera.org/example",
    platform=Platform.COURSERA,
    description="Learn TensorFlow, neural networks, and deployment.",
)


def test_analyze_course_returns_structured_result(fake_llm):
    llm_response = json.dumps(
        {
            "overlap_rate": 20,
            "skill_delta": ["TensorFlow", "Neural Networks"],
            "match_score": 88,
            "verdict": "highly_recommended",
            "reasoning": "Adds deep learning skills relevant to the goal.",
        }
    )
    llm = fake_llm(responses=[llm_response])

    result = analyze_course(PROFILE, COURSE, llm)

    assert result.overlap_rate == 20
    assert "TensorFlow" in result.skill_delta
    assert result.match_score == 88
    assert result.verdict == Verdict.HIGHLY_RECOMMENDED
    assert result.course is COURSE


def test_analyze_course_falls_back_gracefully_on_bad_json(fake_llm):
    llm = fake_llm(responses=["not valid json at all"])

    result = analyze_course(PROFILE, COURSE, llm)

    assert result.verdict == Verdict.PARTIAL_OVERLAP
    assert result.match_score == 0.0


def test_analyze_course_handles_unknown_verdict_value(fake_llm):
    llm_response = json.dumps(
        {
            "overlap_rate": 60,
            "skill_delta": [],
            "match_score": 40,
            "verdict": "somewhat_useful",
            "reasoning": "n/a",
        }
    )
    llm = fake_llm(responses=[llm_response])

    result = analyze_course(PROFILE, COURSE, llm)

    assert result.verdict == Verdict.PARTIAL_OVERLAP


def test_analyze_courses_sorts_by_match_score_desc(fake_llm):
    responses = [
        json.dumps(
            {"overlap_rate": 90, "skill_delta": [], "match_score": 10, "verdict": "redundant", "reasoning": "r1"}
        ),
        json.dumps(
            {
                "overlap_rate": 10,
                "skill_delta": ["Kubernetes"],
                "match_score": 95,
                "verdict": "highly_recommended",
                "reasoning": "r2",
            }
        ),
    ]
    llm = fake_llm(responses=responses)
    courses = [COURSE, Course(title="Course B", url="https://udemy.com/b", platform=Platform.UDEMY)]

    results = analyze_courses(PROFILE, courses, llm)

    assert results[0].match_score == 95
    assert results[1].match_score == 10
