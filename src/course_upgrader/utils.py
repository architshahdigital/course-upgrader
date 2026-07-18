"""Shared utility helpers used across the Course Upgrader engine."""
from __future__ import annotations

import json
import re
from typing import Any


class LLMResponseParseError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""


def extract_json(text: str) -> Any:
    """Extract and parse the first JSON object/array found in an LLM response.

    Handles responses wrapped in markdown code fences (```json ... ```) or
    with leading/trailing commentary text, which LLMs frequently add even
    when explicitly instructed not to.
    """
    text = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    candidate = fence_match.group(1) if fence_match else text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Fall back to scanning for the largest valid JSON object/array substring.
    for i, ch in enumerate(candidate):
        if ch not in "{[":
            continue
        for j in range(len(candidate), i, -1):
            snippet = candidate[i:j]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                continue
        break

    raise LLMResponseParseError(f"Could not parse JSON from LLM response: {text[:200]}...")


def truncate(text: str, max_chars: int = 6000) -> str:
    """Truncate text to a maximum length, appending a marker if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def clean_whitespace(text: str) -> str:
    """Collapse repeated whitespace/blank lines produced by PDF/DOCX extraction."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
