"""Tests for course_searcher.py"""
from __future__ import annotations

import pytest

from course_upgrader.course_searcher import (
    build_search_queries,
    fetch_page_text,
    infer_platform,
    infer_price,
    search_courses,
)
from course_upgrader.models import CandidateProfile, Platform
from course_upgrader.search.base import SearchResult


def test_build_search_queries_defaults_to_all_platforms():
    queries = build_search_queries("Machine Learning Engineer")

    assert "coursera" in queries
    assert queries["coursera"] == 'site:coursera.org "Machine Learning Engineer" course'


def test_build_search_queries_filters_by_platform():
    queries = build_search_queries("Data Science", platforms=["udemy"])

    assert list(queries.keys()) == ["udemy"]


def test_search_courses_requires_career_goal(fake_search):
    profile = CandidateProfile(name=None, raw_text="", career_goal=None)

    with pytest.raises(ValueError):
        search_courses(profile, fake_search())


def test_search_courses_deduplicates_and_infers_platform(fake_search):
    profile = CandidateProfile(name=None, raw_text="", career_goal="Data Science")
    results = [
        SearchResult(title="Free Intro to Data Science", url="https://coursera.org/ds", snippet="free audit available"),
        SearchResult(title="Data Science Bootcamp", url="https://udemy.com/ds", snippet="paid certificate course"),
    ]
    search_provider = fake_search(results=results)

    courses = search_courses(profile, search_provider, platforms=["coursera", "udemy"])

    assert len(courses) == 2
    coursera_course = next(c for c in courses if c.platform == Platform.COURSERA)
    assert coursera_course.price == "free"
    udemy_course = next(c for c in courses if c.platform == Platform.UDEMY)
    assert udemy_course.price == "paid"


def test_infer_platform_matches_known_domain():
    assert infer_platform("https://www.edx.org/course/abc") == Platform.EDX
    assert infer_platform("https://example.com/course/abc") == Platform.OTHER


def test_infer_price_detects_free_and_paid_hints():
    assert infer_price("Free Intro to Python", "audit this course at no cost") == "free"
    assert infer_price("Data Science Professional Certificate", "") == "paid"
    assert infer_price("Some Course", "") is None


def test_fetch_page_text_returns_empty_string_on_invalid_url():
    # No scheme/host to connect to -> requests raises synchronously, no network call made.
    assert fetch_page_text("not-a-valid-url") == ""
