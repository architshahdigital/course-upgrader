"""Tests for server.py using FastAPI's TestClient, with all I/O boundaries faked."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from course_upgrader import server as server_module
from course_upgrader.models import CandidateProfile, Course, CourseAnalysis, Platform, Verdict

client = TestClient(server_module.app)


def _fake_profile() -> CandidateProfile:
    return CandidateProfile(
        name="Jane Doe",
        raw_text="...",
        skills=["Python", "SQL"],
        tools=["pandas"],
        career_goal="Machine Learning Engineer",
    )


def _resume_file():
    return {"resume": ("resume.txt", io.BytesIO(b"Jane Doe\nPython, SQL, pandas"), "text/plain")}


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint_returns_ranked_results(monkeypatch, fake_llm):
    profile = _fake_profile()
    course = Course(title="ML Foundations", url="https://coursera.org/ml", platform=Platform.COURSERA)
    analysis = CourseAnalysis(
        course=course,
        overlap_rate=20,
        skill_delta=["TensorFlow"],
        match_score=90,
        verdict=Verdict.HIGHLY_RECOMMENDED,
        reasoning="Great fit.",
    )

    monkeypatch.setattr(server_module, "get_llm_provider", lambda name=None: fake_llm())
    monkeypatch.setattr(server_module, "read_resume_text", lambda path: "Jane Doe\nPython, SQL, pandas")
    monkeypatch.setattr(server_module, "extract_profile", lambda text, llm, career_goal=None: profile)
    monkeypatch.setattr(server_module, "search_courses", lambda *a, **k: [course])
    monkeypatch.setattr(server_module, "analyze_courses", lambda *a, **k: [analysis])

    response = client.post(
        "/api/analyze",
        data={"goal": "Machine Learning Engineer"},
        files=_resume_file(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["name"] == "Jane Doe"
    assert body["results"][0]["course"]["title"] == "ML Foundations"
    assert body["results"][0]["skill_delta"] == ["TensorFlow"]


def test_analyze_endpoint_rejects_unknown_platform(monkeypatch, fake_llm):
    monkeypatch.setattr(server_module, "get_llm_provider", lambda name=None: fake_llm())

    response = client.post(
        "/api/analyze",
        data={"goal": "Machine Learning Engineer", "platforms": "not-a-real-platform"},
        files=_resume_file(),
    )

    assert response.status_code == 400
    assert "Unknown platform" in response.json()["detail"]


def test_analyze_endpoint_rejects_unsupported_resume_format(fake_llm):
    response = client.post(
        "/api/analyze",
        data={"goal": "Machine Learning Engineer"},
        files={"resume": ("resume.exe", io.BytesIO(b"not a resume"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported resume format" in response.json()["detail"]


def test_check_course_endpoint_returns_single_result(monkeypatch, fake_llm):
    profile = _fake_profile()
    analysis = CourseAnalysis(
        course=Course(title="Advanced Kubernetes", url="https://udemy.com/k8s", platform=Platform.UDEMY),
        overlap_rate=15,
        skill_delta=["Kubernetes", "Helm"],
        match_score=82,
        verdict=Verdict.RECOMMENDED,
        reasoning="Adds container orchestration skills relevant to your goal.",
    )

    monkeypatch.setattr(server_module, "get_llm_provider", lambda name=None: fake_llm())
    monkeypatch.setattr(server_module, "read_resume_text", lambda path: "Jane Doe\nPython, SQL, pandas")
    monkeypatch.setattr(server_module, "extract_profile", lambda text, llm, career_goal=None: profile)
    monkeypatch.setattr(server_module, "analyze_course", lambda profile, course, llm: analysis)

    response = client.post(
        "/api/check-course",
        data={"goal": "Machine Learning Engineer", "course": "https://udemy.com/k8s"},
        files=_resume_file(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["course"]["title"] == "Advanced Kubernetes"
    assert body["result"]["verdict"] == "recommended"
