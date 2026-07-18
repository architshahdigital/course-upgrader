"""Tests for resume_parser.py"""
from __future__ import annotations

import json

import pytest

from course_upgrader.resume_parser import extract_profile, read_resume_text

SAMPLE_RESUME = """Jane Doe
Senior Data Analyst

Experience: 4 years in data analysis using Python, SQL, and Tableau.
Skills: pandas, numpy, scikit-learn, Excel, PowerBI, statistics.
Education: B.S. Computer Science, State University.
"""


def test_read_resume_text_txt(tmp_path):
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text(SAMPLE_RESUME)

    text = read_resume_text(resume_path)

    assert "Jane Doe" in text
    assert "pandas" in text


def test_read_resume_text_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_resume_text(tmp_path / "does_not_exist.pdf")


def test_read_resume_text_unsupported_format(tmp_path):
    bad_path = tmp_path / "resume.xyz"
    bad_path.write_text("hi")

    with pytest.raises(ValueError):
        read_resume_text(bad_path)


def test_extract_profile_parses_llm_json(fake_llm):
    llm_response = json.dumps(
        {
            "name": "Jane Doe",
            "skills": ["Python", "SQL", "statistics"],
            "tools": ["pandas", "numpy", "Tableau"],
            "job_titles": ["Senior Data Analyst"],
            "experience_years": 4,
            "education": ["B.S. Computer Science, State University"],
        }
    )
    llm = fake_llm(responses=[llm_response])

    profile = extract_profile(SAMPLE_RESUME, llm, career_goal="Machine Learning Engineer")

    assert profile.name == "Jane Doe"
    assert "Python" in profile.skills
    assert "pandas" in profile.tools
    assert profile.experience_years == 4
    assert profile.career_goal == "Machine Learning Engineer"


def test_extract_profile_handles_markdown_fenced_json(fake_llm):
    llm_response = "```json\n" + json.dumps({"skills": ["Python"]}) + "\n```"
    llm = fake_llm(responses=[llm_response])

    profile = extract_profile(SAMPLE_RESUME, llm)

    assert profile.skills == ["Python"]


def test_extract_profile_rejects_empty_text(fake_llm):
    llm = fake_llm()
    with pytest.raises(ValueError):
        extract_profile("   \n\n  ", llm)
