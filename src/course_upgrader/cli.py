"""Beautiful terminal CLI for the Course Upgrader agent, powered by `rich`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from course_upgrader.analyzer import analyze_course, analyze_courses
from course_upgrader.config import PLATFORM_DOMAINS
from course_upgrader.course_searcher import fetch_page_text, infer_platform, infer_price, search_courses
from course_upgrader.llm.factory import get_llm_provider
from course_upgrader.models import CandidateProfile, Course, CourseAnalysis, Platform, Verdict
from course_upgrader.resume_parser import extract_profile, read_resume_text
from course_upgrader.search import get_search_provider

console = Console()
if not console.is_terminal:
    # When stdout is piped/redirected (e.g. captured by an agent's shell tool,
    # written to a log file), rich would otherwise fall back to an 80-column
    # width and wrap table cells mid-word. Force a wider, more readable layout.
    console = Console(width=120)

VERDICT_STYLE = {
    Verdict.HIGHLY_RECOMMENDED: ("bold green", "\u2605 HIGHLY RECOMMENDED"),
    Verdict.RECOMMENDED: ("green", "\u2713 RECOMMENDED"),
    Verdict.PARTIAL_OVERLAP: ("yellow", "\u25d0 PARTIAL OVERLAP"),
    Verdict.REDUNDANT: ("bold red", "\u26a0 REDUNDANT"),
}

BANNER = r"""[bold cyan]
   ____                            _   _                           _
  / ___|___  _   _ _ __ ___  ___  | | | |_ __   __ _ _ __ __ _  __| | ___ _ __
 | |   / _ \| | | | '__/ __|/ _ \ | | | | '_ \ / _` | '__/ _` |/ _` |/ _ \ '__|
 | |__| (_) | |_| | |  \__ \  __/ | |_| | |_) | (_| | | | (_| | (_| |  __/ |
  \____\___/ \__,_|_|  |___/\___|  \___/| .__/ \__, |_|  \__,_|\__,_|\___|_|
                                        |_|    |___/
[/bold cyan][dim]        Stop taking redundant courses. Find your real skill delta.[/dim]
"""


@click.group()
@click.version_option(package_name="course-upgrader")
def main() -> None:
    """Course Upgrader \u2014 find courses that actually teach you something new."""


@main.command()
@click.option("--resume", "-r", required=True, type=click.Path(exists=True), help="Path to resume (.pdf, .docx, .txt, .md)")
@click.option("--goal", "-g", required=True, help="Career upgrade goal, e.g. 'Machine Learning Engineer'")
@click.option(
    "--platforms",
    "-p",
    default=None,
    help=f"Comma-separated platforms to search: {', '.join(PLATFORM_DOMAINS)} (default: all)",
)
@click.option("--max-courses", default=5, show_default=True, help="Max courses to fetch per platform")
@click.option("--llm", "llm_provider_name", default=None, help="LLM provider: anthropic | gemini (default from env)")
@click.option("--search", "search_provider_name", default=None, help="Search provider: duckduckgo | tavily (default from env)")
@click.option("--free-only", is_flag=True, help="Only show free courses")
@click.option("--top", default=None, type=int, help="Limit output to top N ranked courses")
@click.option("--json", "json_out", default=None, type=click.Path(), help="Write full JSON results to this path")
def analyze(
    resume: str,
    goal: str,
    platforms: str | None,
    max_courses: int,
    llm_provider_name: str | None,
    search_provider_name: str | None,
    free_only: bool,
    top: int | None,
    json_out: str | None,
) -> None:
    """Analyze a resume against real course listings and rank them by skill delta."""
    console.print(BANNER)

    platform_list = [p.strip().lower() for p in platforms.split(",")] if platforms else None
    invalid = [p for p in (platform_list or []) if p not in PLATFORM_DOMAINS]
    if invalid:
        console.print(f"[bold red]Unknown platform(s): {', '.join(invalid)}[/bold red]")
        console.print(f"Valid platforms: {', '.join(PLATFORM_DOMAINS)}")
        sys.exit(1)

    try:
        llm = get_llm_provider(llm_provider_name)
    except Exception as exc:
        console.print(f"[bold red]LLM provider error:[/bold red] {exc}")
        sys.exit(1)

    profile: CandidateProfile | None = None
    results: list[CourseAnalysis] = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Reading resume...", total=None)

        try:
            raw_text = read_resume_text(resume)
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Failed to read resume:[/bold red] {exc}")
            sys.exit(1)

        progress.update(task, description=f"Extracting profile with {llm.name}...")
        try:
            profile = extract_profile(raw_text, llm, career_goal=goal)
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Failed to extract profile:[/bold red] {exc}")
            sys.exit(1)

        progress.update(task, description="Searching Coursera, Udemy, edX, Simplilearn, Great Learning...")
        try:
            search_provider = get_search_provider(search_provider_name)
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Failed to initialize search provider:[/bold red] {exc}")
            sys.exit(1)
        try:
            courses = search_courses(
                profile, search_provider, platforms=platform_list, max_results_per_platform=max_courses
            )
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Course search failed:[/bold red] {exc}")
            sys.exit(1)

        if not courses:
            progress.stop()
            console.print("[yellow]No courses found. Try a broader career goal or different platforms.[/yellow]")
            sys.exit(0)

        progress.update(task, description=f"Analyzing {len(courses)} courses with {llm.name}...")
        results = analyze_courses(profile, courses, llm)

    if free_only:
        results = [r for r in results if r.course.price == "free"]

    if top:
        results = results[:top]

    _render_profile_panel(profile)
    _render_results_table(results)
    _render_summary(results)

    if json_out:
        Path(json_out).write_text(
            json.dumps({"profile": profile.to_dict(), "results": [r.to_dict() for r in results]}, indent=2)
        )
        console.print(f"\n[dim]Full JSON results written to {json_out}[/dim]")


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the API server to")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind the API server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def server(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI backend server for the web dashboard (web/)."""
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[bold red]uvicorn is not installed.[/bold red] "
            "Run: pip install fastapi uvicorn python-multipart"
        )
        sys.exit(1)

    console.print(BANNER)
    console.print(f"[bold cyan]Starting API server[/bold cyan] at http://{host}:{port}")
    console.print("[dim]Run the frontend separately with: cd web && npm run dev[/dim]\n")
    uvicorn.run("course_upgrader.server:app", host=host, port=port, reload=reload)


@main.command(name="check-course")
@click.option("--resume", "-r", required=True, type=click.Path(exists=True), help="Path to resume (.pdf, .docx, .txt, .md)")
@click.option("--goal", "-g", required=True, help="Career upgrade goal, e.g. 'Machine Learning Engineer'")
@click.option("--course-title", "-t", required=True, help="Name of the specific course to check")
@click.option("--course-url", default="", help="URL of the course (used to fetch its page and infer platform)")
@click.option("--course-description", "-d", default="", help="Syllabus/description text, if you have it")
@click.option(
    "--platform",
    default=None,
    type=click.Choice([p.value for p in Platform]),
    help="Platform hint if it can't be inferred from the URL",
)
@click.option("--llm", "llm_provider_name", default=None, help="LLM provider: anthropic | gemini (default from env)")
@click.option("--json", "json_out", default=None, type=click.Path(), help="Write full JSON result to this path")
def check_course(
    resume: str,
    goal: str,
    course_title: str,
    course_url: str,
    course_description: str,
    platform: str | None,
    llm_provider_name: str | None,
    json_out: str | None,
) -> None:
    """Quickly check whether ONE specific course is worth taking, given your resume."""
    console.print(BANNER)

    try:
        llm = get_llm_provider(llm_provider_name)
    except Exception as exc:
        console.print(f"[bold red]LLM provider error:[/bold red] {exc}")
        sys.exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Reading resume...", total=None)

        try:
            raw_text = read_resume_text(resume)
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Failed to read resume:[/bold red] {exc}")
            sys.exit(1)

        progress.update(task, description=f"Extracting profile with {llm.name}...")
        try:
            profile = extract_profile(raw_text, llm, career_goal=goal)
        except Exception as exc:
            progress.stop()
            console.print(f"[bold red]Failed to extract profile:[/bold red] {exc}")
            sys.exit(1)

        description = course_description
        if not description and course_url:
            progress.update(task, description="Fetching course page...")
            description = fetch_page_text(course_url)

        platform_enum = Platform(platform) if platform else infer_platform(course_url)
        course = Course(
            title=course_title,
            url=course_url or "N/A",
            platform=platform_enum,
            description=description,
            price=infer_price(course_title, description),
        )

        progress.update(task, description=f"Analyzing '{course_title}' with {llm.name}...")
        result = analyze_course(profile, course, llm)

    _render_profile_panel(profile)
    _render_single_result(result)

    if json_out:
        Path(json_out).write_text(json.dumps({"profile": profile.to_dict(), "result": result.to_dict()}, indent=2))
        console.print(f"\n[dim]Full JSON result written to {json_out}[/dim]")


def _render_single_result(result: CourseAnalysis) -> None:
    style, label = VERDICT_STYLE[result.verdict]
    overlap_style = "red" if result.overlap_rate >= 70 else ("yellow" if result.overlap_rate >= 40 else "green")
    body = Text()
    body.append(f"{result.course.title}\n", style="bold")
    body.append(f"{result.course.platform.value} · {result.course.url}\n\n", style="dim")
    body.append("Verdict: ", style="bold")
    body.append(f"{label}\n", style=style)
    body.append("Overlap rate: ", style="bold")
    body.append(f"{result.overlap_rate:.0f}%\n", style=overlap_style)
    body.append("Match score: ", style="bold")
    body.append(f"{result.match_score:.0f}/100\n")
    body.append("Skill delta: ", style="bold")
    body.append(f"{', '.join(result.skill_delta) or 'none'}\n")
    body.append("Reasoning: ", style="bold")
    body.append(result.reasoning)
    console.print(Panel(body, title="[bold]Is this course worth it?[/bold]", border_style=style.replace("bold ", "")))


def _render_profile_panel(profile: CandidateProfile) -> None:
    body = Text()
    body.append("Goal: ", style="bold")
    body.append(f"{profile.career_goal}\n")
    body.append(f"Detected skills ({len(profile.skills)}): ", style="bold")
    body.append(f"{', '.join(profile.skills[:15])}{'...' if len(profile.skills) > 15 else ''}\n")
    body.append(f"Detected tools ({len(profile.tools)}): ", style="bold")
    body.append(f"{', '.join(profile.tools[:15])}{'...' if len(profile.tools) > 15 else ''}")
    console.print(Panel(body, title="[bold]Candidate Profile[/bold]", border_style="cyan"))


def _render_results_table(results: list[CourseAnalysis]) -> None:
    table = Table(title="Course Recommendations", show_lines=True, expand=True)
    table.add_column("Verdict", no_wrap=True)
    table.add_column("Course", overflow="fold", ratio=3)
    table.add_column("Platform", no_wrap=True)
    table.add_column("Price", no_wrap=True)
    table.add_column("Overlap", justify="right", no_wrap=True)
    table.add_column("Match", justify="right", no_wrap=True)
    table.add_column("Skill Delta", overflow="fold", ratio=3)

    for r in results:
        style, label = VERDICT_STYLE[r.verdict]
        price_label = {"free": "[green]FREE[/green]", "paid": "[magenta]PAID[/magenta]"}.get(r.course.price, "?")
        overlap_style = "red" if r.overlap_rate >= 70 else ("yellow" if r.overlap_rate >= 40 else "green")
        table.add_row(
            f"[{style}]{label}[/{style}]",
            f"[link={r.course.url}]{r.course.title}[/link]",
            r.course.platform.value,
            price_label,
            f"[{overlap_style}]{r.overlap_rate:.0f}%[/{overlap_style}]",
            f"{r.match_score:.0f}/100",
            ", ".join(r.skill_delta[:6]) or "[dim]none[/dim]",
        )

    console.print(table)


def _render_summary(results: list[CourseAnalysis]) -> None:
    if not results:
        return
    redundant = sum(1 for r in results if r.verdict == Verdict.REDUNDANT)
    recommended = sum(1 for r in results if r.verdict in (Verdict.RECOMMENDED, Verdict.HIGHLY_RECOMMENDED))
    best = results[0]
    console.print(
        Panel(
            f"[bold]{len(results)}[/bold] courses analyzed \u00b7 "
            f"[green]{recommended} recommended[/green] \u00b7 [red]{redundant} redundant[/red]\n"
            f"Best match: [bold]{best.course.title}[/bold] ({best.match_score:.0f}/100) on {best.course.platform.value}",
            title="[bold]Summary[/bold]",
            border_style="green" if recommended else "yellow",
        )
    )


if __name__ == "__main__":
    main()
