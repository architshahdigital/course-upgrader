"""FastAPI backend powering the Course Upgrader web dashboard.

Exposes the same functionality as the CLI (`analyze` / `check-course`) over
HTTP so the Vite/React frontend in `web/` can drive it interactively.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from course_upgrader.analyzer import analyze_course, analyze_courses
from course_upgrader.config import PLATFORM_DOMAINS
from course_upgrader.course_searcher import fetch_page_text, infer_platform, infer_price, search_courses
from course_upgrader.llm.factory import get_llm_provider
from course_upgrader.models import Course, Platform
from course_upgrader.resume_parser import SUPPORTED_EXTENSIONS, extract_profile, read_resume_text
from course_upgrader.search import get_search_provider

app = FastAPI(title="Course Upgrader API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _save_upload(resume: UploadFile) -> Path:
    """Persist an uploaded resume to a temp file so the existing file-based parser can read it."""
    suffix = Path(resume.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported resume format '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )
    data = await resume.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(data)
    finally:
        tmp.close()
    return Path(tmp.name)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
async def api_analyze(
    resume: UploadFile = File(...),
    goal: str = Form(...),
    platforms: str | None = Form(None),
    max_courses: int = Form(5),
    llm: str | None = Form(None),
    search: str | None = Form(None),
    free_only: bool = Form(False),
) -> dict:
    """Full resume audit: parse resume, search courses, run overlap analysis."""
    tmp_path = await _save_upload(resume)
    try:
        try:
            llm_provider = get_llm_provider(llm)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"LLM provider error: {exc}") from exc

        try:
            raw_text = read_resume_text(tmp_path)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Failed to read resume: {exc}") from exc

        try:
            profile = extract_profile(raw_text, llm_provider, career_goal=goal)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to extract profile: {exc}") from exc

        platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()] if platforms else None
        invalid = [p for p in (platform_list or []) if p not in PLATFORM_DOMAINS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown platform(s): {', '.join(invalid)}")

        try:
            search_provider = get_search_provider(search)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Failed to initialize search provider: {exc}") from exc

        try:
            courses = search_courses(
                profile, search_provider, platforms=platform_list, max_results_per_platform=max_courses
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Course search failed: {exc}") from exc

        results = analyze_courses(profile, courses, llm_provider) if courses else []
        if free_only:
            results = [r for r in results if r.course.price == "free"]

        return {"profile": profile.to_dict(), "results": [r.to_dict() for r in results]}
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/check-course")
async def api_check_course(
    resume: UploadFile = File(...),
    goal: str = Form(...),
    course: str = Form(..., description="Course name or URL"),
    course_description: str = Form(""),
    platform: str | None = Form(None),
    llm: str | None = Form(None),
) -> dict:
    """Quick single-course check: is this one course worth it, given the resume?"""
    tmp_path = await _save_upload(resume)
    try:
        try:
            llm_provider = get_llm_provider(llm)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"LLM provider error: {exc}") from exc

        try:
            raw_text = read_resume_text(tmp_path)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Failed to read resume: {exc}") from exc

        try:
            profile = extract_profile(raw_text, llm_provider, career_goal=goal)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to extract profile: {exc}") from exc

        is_url = course.strip().lower().startswith(("http://", "https://"))
        course_url = course.strip() if is_url else ""
        course_title = course.strip()

        description = course_description
        if not description and course_url:
            description = fetch_page_text(course_url)
            guessed = course_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").strip()
            if guessed:
                course_title = guessed.title()

        if platform:
            try:
                platform_enum = Platform(platform)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"Unknown platform '{platform}'") from exc
        else:
            platform_enum = infer_platform(course_url)

        course_obj = Course(
            title=course_title,
            url=course_url or "N/A",
            platform=platform_enum,
            description=description,
            price=infer_price(course_title, description),
        )

        result = analyze_course(profile, course_obj, llm_provider)
        return {"profile": profile.to_dict(), "result": result.to_dict()}
    finally:
        tmp_path.unlink(missing_ok=True)
