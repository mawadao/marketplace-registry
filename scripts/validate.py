"""Check every listing against the schema and the registry rules. Exits non-zero on any problem."""
from __future__ import annotations

import datetime as dt
import json
import sys

from jsonschema import Draft202012Validator, FormatChecker

from registry import ROOT, SLUG_RE, listing_files, load


def main() -> int:
    schema = json.loads((ROOT / "schema" / "listing.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    problems: list[str] = []
    repos: dict[str, str] = {}
    count = 0

    for kind, path in listing_files():
        count += 1
        rel = path.relative_to(ROOT)
        slug = path.stem
        if not SLUG_RE.match(slug):
            problems.append(f"{rel}: file name must be lowercase letters, digits and hyphens")
        try:
            data = load(path)
        except Exception as exc:  # noqa: BLE001 - report any YAML error
            problems.append(f"{rel}: not valid YAML ({exc})")
            continue
        if not isinstance(data, dict):
            problems.append(f"{rel}: must be a mapping")
            continue
        # YAML turns unquoted dates into date objects; the schema expects strings.
        for key in ("added",):
            if isinstance(data.get(key), dt.date):
                data[key] = data[key].isoformat()
        if isinstance(data.get("safety", {}).get("reviewed_on"), dt.date):
            data["safety"]["reviewed_on"] = data["safety"]["reviewed_on"].isoformat()

        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in err.path) or "(top)"
            problems.append(f"{rel}: {where}: {err.message}")

        if data.get("kind") != kind:
            problems.append(f"{rel}: kind must be '{kind}' for files in {path.parent.name}/")
        if kind == "agent" and data.get("pricing", {}).get("education", {}).get("price") != "free":
            problems.append(f"{rel}: agents must be free for education (pricing.education.price: free)")
        added = data.get("added")
        if isinstance(added, str) and added > dt.date.today().isoformat():
            problems.append(f"{rel}: added is in the future")

        repo = (data.get("links") or {}).get("repository")
        if repo:
            key = repo.rstrip("/").lower()
            if key in repos:
                problems.append(f"{rel}: repository already listed in {repos[key]}")
            repos[key] = str(rel)

    for p in problems:
        print(p)
    print(f"{count} listings checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
