"""Fetch public GitHub facts for many repositories with batched GraphQL queries."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request

GITHUB_RE = re.compile(r"^https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9._-]+?)(?:\.git)?/?$")
FIELDS = """
  nameWithOwner description homepageUrl stargazerCount forkCount isArchived pushedAt
  licenseInfo { spdxId }
  primaryLanguage { name }
  repositoryTopics(first: 10) { nodes { topic { name } } }
"""


def parse(url: str) -> tuple[str, str] | None:
    m = GITHUB_RE.match(url or "")
    return (m.group(1), m.group(2)) if m else None


def _query(token: str, body: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": body}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "mawadao-registry"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception:  # noqa: BLE001 - retry transient network errors
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    return {}


def fetch(urls: list[str], token: str | None = None, batch: int = 50) -> dict[str, dict]:
    """Map each GitHub URL to its facts. Missing or private repositories are left out."""
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN to fetch repository stats")
    pairs = {u: parse(u) for u in urls}
    wanted = [(u, p) for u, p in pairs.items() if p]
    out: dict[str, dict] = {}
    for i in range(0, len(wanted), batch):
        chunk = wanted[i : i + batch]
        parts = [
            f'r{n}: repository(owner: {json.dumps(o)}, name: {json.dumps(r)}) {{ {FIELDS} }}'
            for n, (_, (o, r)) in enumerate(chunk)
        ]
        data = _query(token, "query {" + "\n".join(parts) + "}").get("data") or {}
        for n, (url, _) in enumerate(chunk):
            repo = data.get(f"r{n}")
            if not repo:
                continue
            out[url] = {
                "full_name": repo["nameWithOwner"],
                "description": repo["description"],
                "homepage": repo["homepageUrl"] or None,
                "stars": repo["stargazerCount"],
                "forks": repo["forkCount"],
                "archived": repo["isArchived"],
                "pushed_at": repo["pushedAt"],
                "license": (repo["licenseInfo"] or {}).get("spdxId"),
                "language": (repo["primaryLanguage"] or {}).get("name"),
                "topics": [t["topic"]["name"] for t in repo["repositoryTopics"]["nodes"]],
            }
    return out
