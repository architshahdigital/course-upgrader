"""Tests for cli.py using click's CliRunner, with all I/O boundaries faked."""
from __future__ import annotations

from click.testing import CliRunner

from course_upgrader import cli as cli_module
from course_upgrader.models import CandidateProfile, Course, CourseAnalysis, Platform, Verdict


def _fake_profile() -> CandidateProfile:
    return CandidateProfile(
        name="Jane Doe",
        raw_text="...",
        skills=["Python", "SQL"],
        tools=["pandas"],
        career_goal="Machine Learning Engineer",
    )


def test_analyze_command_renders_results_table(monkeypatch, tmp_path, fake_llm):
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text("Jane Doe\nPython, SQL, pandas")

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

    monkeypatch.setattr(cli_module, "get_llm_provider", lambda name=None: fake_llm())
    monkeypatch.setattr(cli_module, "read_resume_text", lambda path: resume_path.read_text())
    monkeypatch.setattr(cli_module, "extract_profile", lambda text, llm, career_goal=None: profile)
    monkeypatch.setattr(cli_module, "search_courses", lambda *a, **k: [course])
    monkeypatch.setattr(cli_module, "analyze_courses", lambda *a, **k: [analysis])

    runner = CliRunner()
    result = runner.invoke(cli_module.main, ["analyze", "-r", str(resume_path), "-g", "Machine Learning Engineer"])

    assert result.exit_code == 0
    # Rich may wrap narrow table cells mid-word in a non-tty test terminal, so
    # compare against a whitespace-stripped version of the output.
    normalized = "".join(result.output.split())
    assert "MLFoundations" in normalized
    assert "TensorFlow" in normalized


def test_check_course_command_renders_single_result(monkeypatch, tmp_path, fake_llm):
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text("Jane Doe\nPython, SQL, pandas")

    profile = _fake_profile()
    analysis = CourseAnalysis(
        course=Course(title="Advanced Kubernetes", url="https://udemy.com/k8s", platform=Platform.UDEMY),
        overlap_rate=15,
        skill_delta=["Kubernetes", "Helm"],
        match_score=82,
        verdict=Verdict.RECOMMENDED,
        reasoning="Adds container orchestration skills relevant to your goal.",
    )

    monkeypatch.setattr(cli_module, "get_llm_provider", lambda name=None: fake_llm())
    monkeypatch.setattr(cli_module, "read_resume_text", lambda path: resume_path.read_text())
    monkeypatch.setattr(cli_module, "extract_profile", lambda text, llm, career_goal=None: profile)
    monkeypatch.setattr(cli_module, "analyze_course", lambda profile, course, llm: analysis)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.main,
        [
            "check-course",
            "-r",
            str(resume_path),
            "-g",
            "Machine Learning Engineer",
            "-t",
            "Advanced Kubernetes",
            "--course-url",
            "https://udemy.com/k8s",
        ],
    )

    assert result.exit_code == 0
    assert "Advanced Kubernetes" in result.output
    assert "Kubernetes" in result.output
    assert "RECOMMENDED" in result.output
