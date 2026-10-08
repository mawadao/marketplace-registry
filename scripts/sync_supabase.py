"""Sync dist/index.json into Supabase's marketplace_listings table.

Every listing in the index is upserted (so a merged pull request adds or updates its
row), and any row whose (kind, slug) is no longer in the index is deleted (so a merged
removal clears its row). Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY; if the key
isn't set, this is a no-op, so the step can run before the secret is configured.

Usage: python scripts/sync_supabase.py [dist/index.json]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

TABLE = "marketplace_listings"
ROW_FIELDS = (
    "kind", "slug", "name", "summary", "description", "category", "tags", "links",
    "license", "skill_level", "pricing", "agent", "maintainer", "safety", "added", "stats",
)


def request(method: str, base_url: str, key: str, params: str = "", body=None, prefer: str | None = None) -> tuple[int, bytes]:
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(
        f"{base_url}/rest/v1/{TABLE}{params}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def row_for(listing: dict) -> dict:
    return {field: listing.get(field) for field in ROW_FIELDS if field in listing or field == "stats"}


def main() -> int:
    base_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        print("SUPABASE_SERVICE_ROLE_KEY not set, skipping database sync")
        return 0
    if not base_url:
        print("SUPABASE_URL not set", file=sys.stderr)
        return 1

    index_path = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/index.json")
    listings = json.loads(index_path.read_text()).get("listings", [])
    current = {(item["kind"], item["slug"]) for item in listings}

    if listings:
        rows = [row_for(item) for item in listings]
        status, body = request(
            "POST", base_url, key,
            params="?on_conflict=kind,slug",
            body=rows,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        if status >= 300:
            print(f"upsert failed: {status} {body.decode(errors='replace')}", file=sys.stderr)
            return 1

    status, body = request("GET", base_url, key, params="?select=kind,slug")
    if status >= 300:
        print(f"could not list existing rows: {status} {body.decode(errors='replace')}", file=sys.stderr)
        return 1
    existing = {(row["kind"], row["slug"]) for row in json.loads(body)}

    removed = existing - current
    for kind, slug in removed:
        status, body = request(
            "DELETE", base_url, key,
            params=f"?kind=eq.{kind}&slug=eq.{slug}",
            prefer="return=minimal",
        )
        if status >= 300:
            print(f"could not remove {kind}/{slug}: {status} {body.decode(errors='replace')}", file=sys.stderr)
            return 1

    print(f"synced {len(listings)} listing(s) to Supabase, removed {len(removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
