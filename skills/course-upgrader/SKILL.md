---
name: course-upgrader
description: Audits a candidate's resume against real, live course listings on Coursera, Udemy, edX, Simplilearn, Great Learning, and Google Digital Garage to determine which courses teach genuinely new skills versus content the candidate already knows. Computes an Overlap Rate, Skill Delta, and personalized Match Score for every course. Use this skill whenever the user asks things like "should I take this course", "is [course name] worth it for my resume/career", "what course should I take to become a [role]", "find me courses for [career goal] that aren't redundant", "compare my resume against this course/syllabus", or wants a career-upgrade, upskilling, or reskilling course audit / recommendation.
---

# Course Upgrader

Stops the user from wasting time and money on redundant courses. This skill wraps the `course-upgrader` Python CLI, which parses a resume, searches real course listings, and runs an LLM-driven overlap analysis for each course: **Overlap Rate** (% already known), **Skill Delta** (specific new tools/concepts gained), and a personalized **Match Score** (0-100).

## Fallback: Running in Cloud/Web Environments (e.g., Claude.ai, CoWork, Custom Prompt)

If you are running in a cloud or web-based chat environment (such as the Claude.ai web app or CoWork) where terminal/bash access is unavailable, do NOT attempt to run setup checks or CLI commands. Instead, perform the course upgrade analysis manually directly within your conversation context using these instructions:

1. **Ingest Candidate Profile:** Parse the candidate's uploaded resume (or pasted text) to extract their name, current skills, specific tools/libraries/frameworks, and career goals.
2. **Discover Courses (Web Search):** Use your built-in web search/browsing capabilities (or ask the user to provide course URLs/syllabi) to search Coursera, Udemy, edX, Simplilearn, Great Learning, and Google Digital Garage for course listings relevant to the goal.
3. **Evaluate Overlap & Delta (In-Context):** Compare each course's content/syllabus against the candidate's profile:
   - Compute the **Overlap Rate (%)** (how much of the course they already know).
   - Identify the **Skill Delta** (specific new tools/concepts/frameworks they will gain).
   - Estimate a personalized **Match Score (0-100)** based on goal relevance.
   - Assign a **Verdict** (`highly_recommended`, `recommended`, `partial_overlap`, or `redundant`).
4. **Present Recommendations:** Group, rank, and present the recommendations (free vs. paid) in a clean markdown format as described in **Workflow 1 (Step 5)** or **Workflow 2 (Step 3)**.

---

## Setup check (do this once per session, before the first run)

Determine where the `course-upgrader` CLI lives, trying each of these in order:

```bash
CLI=""
if command -v course-upgrader >/dev/null 2>&1; then
  CLI="course-upgrader"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -x "${CLAUDE_PLUGIN_ROOT}/.venv/bin/course-upgrader" ]; then
  CLI="${CLAUDE_PLUGIN_ROOT}/.venv/bin/course-upgrader"
elif [ -f "$HOME/.claude/skills/course-upgrader/.cli_path" ]; then
  CLI="$(cat "$HOME/.claude/skills/course-upgrader/.cli_path")"
elif [ -f "./skills/course-upgrader/.cli_path" ]; then
  CLI="$(cat "./skills/course-upgrader/.cli_path")"
fi

if [ -z "$CLI" ] || ! "$CLI" --help >/dev/null 2>&1; then
  echo "not-installed"
fi
```

If it prints `not-installed`, tell the user the CLI isn't set up yet and offer to run the installer for them:

```bash
bash "${CLAUDE_PLUGIN_ROOT:-.}/scripts/install.sh"
```

(If you're working directly inside the `course-upgrader` source repo rather than as an installed plugin, just run `bash scripts/install.sh` from the repo root.)

Once installed, also confirm an LLM API key is configured — check for `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` in the environment or in a `.env` file next to the CLI's project root. If neither is set, ask the user which provider they want to use (Anthropic is the default) and help them add the key to `.env`. **Never print, log, or echo back the key value itself.**

For every command below, substitute `$CLI` with whatever path you resolved above.

## Workflow 1 — Full resume audit

Use this when the user wants a broad course search or upskilling audit: "what should I take next", "find me courses for X", "audit my resume", "what's my skill gap for [role]".

1. **Find the resume.** Use the Glob tool to look for common filenames in the current workspace first: `resume.pdf`, `resume.docx`, `Resume*.{pdf,docx,txt}`, `cv.pdf`, etc. If nothing is found, ask the user for a file path, or ask them to paste their resume text so you can save it to a temporary `.txt` file yourself.
2. **Get the career goal.** Ask directly if it isn't already clear from the conversation: "What role or skill are you upgrading toward?" (e.g. "Machine Learning Engineer", "Cloud/DevOps", "Product Management").
3. **Run the CLI**, always with `--json` so you can parse structured results reliably — the colored terminal table is meant for a human reading their own terminal, not for you to parse:
   ```bash
   "$CLI" analyze --resume "<resume_path>" --goal "<career goal>" --json /tmp/course-upgrader-results.json
   ```
   Pass along extra flags based on what the user asks for:
   - `--free-only` — user only wants free courses
   - `--platforms coursera,udemy` — user named specific platforms (valid values: `coursera`, `udemy`, `edx`, `simplilearn`, `great_learning`, `google_digital_garage`)
   - `--max-courses N` — user wants a broader or narrower search
   - `--llm gemini` — user prefers Gemini over the default Anthropic provider
4. **Read the JSON file** (Read tool) and parse it. Shape:
   ```json
   {
     "profile": { "name": "...", "skills": ["..."], "tools": ["..."], "career_goal": "..." },
     "results": [
       {
         "course": { "title": "...", "url": "...", "platform": "...", "description": "...", "price": "free|paid|null", "provider": null },
         "overlap_rate": 0,
         "skill_delta": ["..."],
         "match_score": 0,
         "verdict": "highly_recommended | recommended | partial_overlap | redundant",
         "reasoning": "..."
       }
     ]
   }
   ```
5. **Present it like a career coach, not a data dump:**
   - Open with a one-line summary of what was detected on their resume and their stated goal.
   - Lead with the top 2-3 `highly_recommended` / `recommended` courses. For each: name, platform, link, price, and 2-4 concrete bullet points straight from `skill_delta` explaining what's actually new.
   - Group `redundant` courses into a short "skip these" list, one line each using the `reasoning` field, so the user avoids wasting money or time.
   - Mention the free-vs-paid split if relevant.
   - Offer to run a deeper single-course check (Workflow 2) or re-run for a different career goal.

## Workflow 2 — Quick single-course check

Use this when the user asks about **one specific course** by name or URL: "Is [Course Name] worth it for me?", "Should I take this Udemy course: `<url>`?"

1. If you don't already have the user's resume/goal from earlier in this conversation, get them first (Workflow 1, steps 1-2) — you don't need to run a full multi-platform search for a single-course check.
2. Run the dedicated command:
   ```bash
   "$CLI" check-course --resume "<resume_path>" --goal "<career goal>" \
     --course-title "<course name>" \
     --course-url "<url, if the user gave one>" \
     --course-description "<paste the syllabus/description here, if the user gave you one>" \
     --json /tmp/course-upgrader-check.json
   ```
   - If the user only gave a URL, omit `--course-description` — the CLI will best-effort fetch and use the page's text itself.
   - If the user only gave a course name with no URL, omit `--course-url`; ask the user to paste the syllabus or description for a more accurate read if they have one.
3. Read the JSON result and answer directly and concisely — this is a yes/no question, so lead with the verdict, then back it up with the overlap rate, the specific skill delta, and a one-line recommendation in plain language.

## Troubleshooting

- **"course-upgrader: command not found" / setup check prints `not-installed`** → run the installer (see Setup check above).
- **"ANTHROPIC_API_KEY is not set" / "GEMINI_API_KEY is not set"** → help the user add it to the project's `.env` file (never echo the key value back).
- **"No courses found."** → suggest a broader or differently-worded career goal, or fewer platform restrictions.
- **PDF resume extraction returns no text** → it's likely a scanned/image-only PDF; ask the user for a `.docx` or `.txt` version instead.
