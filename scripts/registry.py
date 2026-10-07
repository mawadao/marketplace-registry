"""Shared helpers for loading listings."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KIND_DIRS = {"tool": ROOT / "tools", "agent": ROOT / "agents"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

CATEGORIES = {
    "agents": "AI agents",
    "llm-apps": "RAG & LLM apps",
    "coding": "Coding assistants",
    "local-llms": "Run LLMs locally",
    "chat": "Chat interfaces",
    "image": "Image generation",
    "video": "Video generation",
    "speech": "Speech & voice",
    "documents": "Documents & OCR",
    "search": "AI search",
    "vector-databases": "Vector databases",
    "ml-platforms": "Training & MLOps",
    "robotics": "Robotics",
    "browser-automation": "Browser automation",
    "no-code": "No-code builders",
    "learning": "Learn AI",
    "mcp-servers": "MCP servers",
    "education": "Education",
    "other": "Other",
}

AUDIENCES = {
    "education": "Students, teachers & non-profits",
    "individuals": "Individuals",
    "business": "Companies & businesses",
}


def listing_files():
    for kind, folder in KIND_DIRS.items():
        for path in sorted(folder.glob("*.yaml")):
            yield kind, path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)
