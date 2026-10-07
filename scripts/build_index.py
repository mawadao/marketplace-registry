"""Build dist/index.json: every listing plus live GitHub stats and trending deltas.

Usage: python scripts/build_index.py [--previous URL_OR_PATH] [--weekly] [--no-stats]
--previous points at the last published index.json. With --weekly, "trending" becomes the stars
gained since the previous weekly baseline and the baseline moves to now; without it, trending and
the baseline are carried over so builds between weekly runs don't reset them.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path

from github_stats import fetch
from registry import AUDIENCES, CATEGORIES, ROOT, listing_files, load


def read_previous(source: str | None) -> dict[str, dict]:
    if not source:
        return {}
    try:
        if source.startswith("http"):
            with urllib.request.urlopen(source, timeout=60) as resp:
                data = json.load(resp)
        else:
            data = json.loads(Path(source).read_text())
    except Exception as exc:  # noqa: BLE001 - first build has nothing to compare with
        print(f"no previous index ({exc}); trending will be empty")
        return {}
    return {item["slug"]: item for item in data.get("listings", [])}


def jsonable(value):
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    return value


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--previous")
    ap.add_argument("--weekly", action="store_true")
    ap.add_argument("--no-stats", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "dist" / "index.json"))
    args = ap.parse_args()

    listings = []
    for kind, path in listing_files():
        item = jsonable(load(path))
        item["slug"] = path.stem
        listings.append(item)

    repos = [i["links"].get("repository") for i in listings if i["links"].get("repository")]
    stats = {} if args.no_stats else fetch(repos)
    previous = read_previous(args.previous)
    generated = dt.datetime.now(dt.timezone.utc)

    for item in listings:
        s = stats.get(item["links"].get("repository") or "")
        if s:
            prev = previous.get(item["slug"], {}).get("stats") or {}
            base = prev.get("baseline") or {}
            now = generated.isoformat(timespec="seconds")
            if args.weekly or not base:
                gained = s["stars"] - base["stars"] if isinstance(base.get("stars"), int) else None
                trend = {"stars_gained": gained, "since": base.get("at") if gained is not None else None}
                base = {"stars": s["stars"], "at": now}
            else:
                trend = {"stars_gained": prev.get("stars_gained"), "since": prev.get("since")}
            item["stats"] = {
                "stars": s["stars"],
                "forks": s["forks"],
                "language": s["language"],
                "pushed_at": s["pushed_at"],
                "archived": s["archived"],
                **trend,
                "baseline": base,
                "checked_at": now,
            }

    listings.sort(key=lambda i: (i["kind"], -(i.get("stats") or {}).get("stars", 0), i["slug"]))
    index = {
        "generated_at": generated.isoformat(timespec="seconds"),
        "categories": CATEGORIES,
        "audiences": AUDIENCES,
        "counts": {
            "tools": sum(1 for i in listings if i["kind"] == "tool"),
            "agents": sum(1 for i in listings if i["kind"] == "agent"),
        },
        "listings": listings,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {out} with {len(listings)} listings ({len(stats)} with GitHub stats)")


if __name__ == "__main__":
    main()
