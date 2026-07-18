#!/usr/bin/env bash
# Installs the course-upgrader CLI and registers its Claude Skill.
#
# What this does:
#   1. Finds a Python 3.10+ interpreter.
#   2. Creates a project-local virtualenv at $PROJECT_ROOT/.venv.
#   3. Installs course-upgrader (editable) + dependencies into it.
#   4. Verifies the `course-upgrader` console script works.
#   5. Writes a `.cli_path` marker file inside skills/course-upgrader/ so the
#      skill can find this venv's CLI even after being copied elsewhere
#      (e.g. into ~/.claude/skills).
#   6. Sets up a `.env` file from `.env.example` if one doesn't exist yet.
#   7. Installs (symlinks, falling back to copying) the skill into
#      ~/.claude/skills/course-upgrader so Claude Code picks it up.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
SKILL_SRC="$PROJECT_ROOT/skills/course-upgrader"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
SKILL_DEST="$CLAUDE_SKILLS_DIR/course-upgrader"

echo "==> Installing course-upgrader from $PROJECT_ROOT"

# 1. Find a Python 3.10+ interpreter.
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0.0")"
    major="${version%%.*}"
    minor="${version##*.}"
    if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: could not find a Python 3.10+ interpreter on PATH." >&2
  echo "Please install Python 3.10 or newer and re-run this script." >&2
  exit 1
fi
echo "==> Using $PYTHON_BIN ($("$PYTHON_BIN" --version))"

# 2. Create the virtualenv.
if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtualenv at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "==> Reusing existing virtualenv at $VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_CLI="$VENV_DIR/bin/course-upgrader"

# 3. Install dependencies + the package itself (editable).
echo "==> Upgrading pip"
"$VENV_PY" -m pip install --upgrade pip --quiet

echo "==> Installing course-upgrader and its dependencies"
"$VENV_PIP" install -e "$PROJECT_ROOT" --quiet

# 4. Verify the console script works.
if ! "$VENV_CLI" --help >/dev/null 2>&1; then
  echo "ERROR: course-upgrader CLI did not install correctly at $VENV_CLI" >&2
  exit 1
fi
echo "==> course-upgrader CLI installed at $VENV_CLI"

# 5. Write the .cli_path marker file for the skill fallback lookup.
mkdir -p "$SKILL_SRC"
echo "$VENV_CLI" > "$SKILL_SRC/.cli_path"
echo "==> Wrote CLI path marker to $SKILL_SRC/.cli_path"

# 6. Set up .env from .env.example if missing.
if [ ! -f "$PROJECT_ROOT/.env" ] && [ -f "$PROJECT_ROOT/.env.example" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo "==> Created .env from .env.example — add your ANTHROPIC_API_KEY or GEMINI_API_KEY there."
fi

# 7. Install the skill into ~/.claude/skills (symlink, falling back to copy).
mkdir -p "$CLAUDE_SKILLS_DIR"
if [ -L "$SKILL_DEST" ] || [ -e "$SKILL_DEST" ]; then
  echo "==> Removing existing skill install at $SKILL_DEST"
  rm -rf "$SKILL_DEST"
fi

if ln -s "$SKILL_SRC" "$SKILL_DEST" 2>/dev/null; then
  echo "==> Symlinked skill into $SKILL_DEST"
else
  cp -R "$SKILL_SRC" "$SKILL_DEST"
  echo "==> Copied skill into $SKILL_DEST (symlink not supported on this filesystem)"
fi

echo ""
echo "Done! course-upgrader is installed and the Claude Skill is registered."
echo "CLI: $VENV_CLI"
echo "Skill: $SKILL_DEST"
echo ""
echo "If you haven't already, add ANTHROPIC_API_KEY or GEMINI_API_KEY to:"
echo "  $PROJECT_ROOT/.env"
