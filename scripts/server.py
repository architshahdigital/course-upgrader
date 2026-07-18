#!/usr/bin/env python
"""Thin launcher for the Course Upgrader FastAPI backend.

Usage:
    python scripts/server.py [--host HOST] [--port PORT] [--reload]

Equivalent to running `course-upgrader server`.
"""
from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Course Upgrader API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run("course_upgrader.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
