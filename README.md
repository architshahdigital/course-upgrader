# Course Upgrader

**Stop taking redundant courses.** Course Upgrader compares your resume against real, live course listings (Coursera, Udemy, edX, Simplilearn, Great Learning, Google Digital Garage) and tells you exactly which ones will teach you something you *don't already know* — with a quantified **Overlap Rate**, **Skill Delta**, and personalized **Match Score**.

> **Status:** Phase 1 (Core Python Engine + CLI), Phase 2 (Claude Skill / Plugin packaging), and Phase 3 (FastAPI backend + React Web Dashboard) are all complete.

---

## How it works

1. **Resume & Goal Ingestion** — parses your resume (`.pdf`, `.docx`, `.txt`, `.md`) and, together with your stated career goal, uses an LLM to extract a structured profile: skills, tools, job titles, experience, education.
2. **Real-time Web Search** — runs `site:`-scoped DuckDuckGo searches against each target platform to find real, current course listings for your goal.
3. **Semantic Overlap Engine** — an LLM compares each course against your profile and returns:
   - **Overlap Rate (%)** — how much of the course you already know.
   - **Skill Delta** — the specific new tools/concepts/frameworks you'd gain.
   - **Match Score (0–100)** — personalized value-for-time/money.
   - **Verdict** — `highly_recommended`, `recommended`, `partial_overlap`, or `redundant`.
4. **Rich Terminal Output** — a polished `rich`-powered CLI table with color-coded overlap warnings, ranked by match score.

## Architecture

The engine is **provider-agnostic** on two axes so you're never locked in:

- **LLM provider** (`course_upgrader/llm/`): `AnthropicProvider` (default) or `GeminiProvider`, behind a shared `LLMProvider` interface. Swap with `--llm anthropic|gemini` or the `COURSE_UPGRADER_LLM_PROVIDER` env var.
- **Search provider** (`course_upgrader/search/`): `DuckDuckGoProvider` (default, free, no API key) behind a shared `SearchProvider` interface, ready to be swapped for Tavily/Brave/Google Custom Search later.

```
src/course_upgrader/
├── config.py            # env-driven settings, platform domain map
├── models.py             # CandidateProfile, Course, CourseAnalysis, enums
├── utils.py               # robust JSON extraction from LLM text, text cleanup
├── llm/
│   ├── base.py            # LLMProvider abstract interface
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   └── factory.py         # get_llm_provider() — picks provider from env/flag
├── search/
│   ├── base.py            # SearchProvider abstract interface
│   └── duckduckgo_provider.py
├── resume_parser.py       # file -> raw text -> CandidateProfile (LLM-assisted)
├── course_searcher.py     # CandidateProfile -> list[Course] via site: searches
├── analyzer.py             # (profile, course) -> CourseAnalysis via LLM
├── server.py               # FastAPI backend for the web dashboard
└── cli.py                  # `analyze` / `check-course` / `server` commands — rich terminal UI

skills/course-upgrader/SKILL.md   # Claude Skill definition (auto-discovered)
.claude-plugin/plugin.json        # Claude Code plugin manifest
.claude-plugin/marketplace.json   # Claude Code marketplace manifest
scripts/install.sh                 # venv + CLI + skill installer
scripts/server.py                  # thin launcher for the FastAPI backend
web/                                # Vite + React + TypeScript + Tailwind + Framer Motion dashboard
```

## Installation

```bash
cd course-upgrader
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY (or GEMINI_API_KEY)
```

## Usage

```bash
course-upgrader analyze \
  --resume path/to/resume.pdf \
  --goal "Machine Learning Engineer"
```

Options:

| Flag | Description |
|---|---|
| `-r, --resume` | Path to `.pdf` / `.docx` / `.txt` / `.md` resume (required) |
| `-g, --goal` | Career upgrade goal, e.g. `"Data Engineer"` (required) |
| `-p, --platforms` | Comma-separated subset of `coursera,udemy,edx,simplilearn,great_learning,google_digital_garage` (default: all) |
| `--max-courses` | Max courses fetched per platform (default: 5) |
| `--llm` | `anthropic` or `gemini` (default: `COURSE_UPGRADER_LLM_PROVIDER` env, else `anthropic`) |
| `--free-only` | Only show courses inferred as free |
| `--top N` | Limit output to the top N ranked courses |
| `--json PATH` | Also write full structured results to a JSON file |

Example with the bundled sample resume:

```bash
course-upgrader analyze -r tests/fixtures/sample_resume.txt -g "Machine Learning Engineer" --top 10 --json results.json
```

### Quick single-course check

Already found a course and just want to know if it's worth it? Skip the broad platform search:

```bash
course-upgrader check-course \
  --resume path/to/resume.pdf \
  --goal "Machine Learning Engineer" \
  --course-title "Advanced Kubernetes for ML Deployment" \
  --course-url "https://udemy.com/course/example" \
  --json check.json
```

If `--course-description` isn't provided, the CLI best-effort fetches and reads the page text from `--course-url`. Options mirror `analyze`: `-r/--resume`, `-g/--goal`, `--llm`, `--json`, plus `-t/--course-title`, `--course-url`, `-d/--course-description`, `--platform`.

## Claude Skill & Plugin

Course Upgrader ships as a Claude Code Skill and Plugin, so Claude can run audits and single-course checks for you directly in conversation.

**Install:**

```bash
bash scripts/install.sh
```

This sets up a project-local `.venv`, installs the CLI, and installs the skill into `~/.claude/skills/course-upgrader` (symlinked, so it stays in sync with this repo). It also creates `.env` from `.env.example` if one doesn't exist yet — add your `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` there.

Once installed, just ask Claude things like:

- "Should I take this course: `<url>`?"
- "What courses should I take to become a Cloud/DevOps engineer?"
- "Audit my resume against free courses on Coursera and edX."

See `skills/course-upgrader/SKILL.md` for the full workflow Claude follows. This repo also doubles as a Claude Code Plugin (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`) so it can be installed via the plugin/marketplace system.

## Web Dashboard

A local FastAPI backend + Vite/React frontend give you a visual alternative to the CLI: drag-and-drop your resume, pick a goal, and browse course recommendations as glowing, color-coded cards with a redundancy meter.

**1. Start the API backend** (from the project root, with `.venv` set up as above):

```bash
course-upgrader server
# or: python scripts/server.py
```

This starts the FastAPI app at `http://127.0.0.1:8000`, exposing:

| Endpoint | Description |
|---|---|
| `POST /api/analyze` | multipart form: `resume` (file), `goal`, optional `platforms`, `max_courses`, `llm`, `free_only` — full audit |
| `POST /api/check-course` | multipart form: `resume` (file), `goal`, `course` (name or URL), optional `course_description`, `platform`, `llm` — single-course check |
| `GET /api/health` | health check |

Flags: `--host`, `--port` (default `8000`), `--reload` for development auto-reload.

**2. Start the frontend** (in a separate terminal):

```bash
cd web
npm install   # first time only
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8000`, so both must be running.

**Frontend stack:** Vite + React + TypeScript + Tailwind CSS v4 + Framer Motion + lucide-react. Dark theme with glassmorphism panels, a circular redundancy meter per course, animated tabs for free/paid filtering, and a detail modal comparing your current skills against each course's skill delta side by side.

To build a production bundle: `cd web && npm run build` (outputs to `web/dist/`).

## Configuration

All configuration is via environment variables (or a `.env` file — see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `COURSE_UPGRADER_LLM_PROVIDER` | `anthropic` or `gemini` | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `ANTHROPIC_MODEL` | Claude model id | `claude-sonnet-4-6` |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `GEMINI_MODEL` | Gemini model id | `gemini-2.5-flash` |
| `COURSE_UPGRADER_MAX_PER_PLATFORM` | Default max courses per platform | `5` |
| `COURSE_UPGRADER_TIMEOUT` | Network timeout (seconds) | `15` |

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests use fake `LLMProvider`/`SearchProvider` implementations (see `tests/conftest.py`) so the suite runs fully offline — no API keys or network access required.

## Roadmap

- **Phase 1 (done):** Core Python engine + rich terminal CLI.
- **Phase 2 (done):** Package as a Claude Skill (`SKILL.md` + scripts) so the audit can be invoked directly inside Claude Code.
- **Phase 3 (done):** FastAPI backend + React/Vite/Tailwind/Framer Motion web dashboard visualizing skill gaps and course recommendations.

## License

MIT
