#!/usr/bin/env python3
"""Report drift between registry.json and each tool repo's GitHub About
section (description, homepage, topics). Report-only: it never edits a
repo, because applying changes needs an admin-scoped token per repo.

Usage:
  python scripts/check_fleet_about.py            # human-readable report
  python scripts/check_fleet_about.py --json     # machine-readable
  python scripts/check_fleet_about.py --strict   # exit 1 when anything drifts
  python scripts/check_fleet_about.py --wording  # also show description wording diffs

Requires the GitHub CLI (`gh`) authenticated with read access.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent

Fetcher = Callable[[str], "dict[str, Any] | None"]


def fetch_repo(repo: str) -> "dict[str, Any] | None":
    result = subprocess.run(
        ["gh", "repo", "view", repo, "--json", "description,homepageUrl,repositoryTopics"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout or "{}")
    return {
        "description": (data.get("description") or "").strip(),
        "homepage": (data.get("homepageUrl") or "").strip(),
        "topics": sorted(t["name"] for t in (data.get("repositoryTopics") or [])),
    }


_COUNT_PATTERNS = {
    "skills": re.compile(r"(\d+)\s+(?:AI\s+)?skills\b", re.IGNORECASE),
    "rules": re.compile(r"(\d+)\s+rules\b", re.IGNORECASE),
    "mcpTools": re.compile(r"(\d+)\s+(?:MCP\s+)?tools\b", re.IGNORECASE),
}


def stale_counts(entry: dict[str, Any], description: str) -> list[str]:
    """Counts quoted in a GitHub description that contradict the registry."""
    out = []
    for field, pattern in _COUNT_PATTERNS.items():
        for match in pattern.finditer(description):
            quoted = int(match.group(1))
            actual = int(entry.get(field) or 0)
            if actual and quoted != actual:
                out.append(f"description says {match.group(0)!r} but registry has {field}={actual}")
    return out


def compare(entry: dict[str, Any], live: "dict[str, Any] | None", *, wording: bool = False) -> list[str]:
    """Human-readable differences between a registry entry and live About data.

    Always flagged: unreadable repo, empty description or topics, counts in
    the description that contradict the registry, homepage mismatch, and
    registry topics missing on GitHub. Wording differences are only reported
    with ``wording=True``; GitHub descriptions are often deliberately richer."""
    if live is None:
        return ["could not read repository (missing, private, or no access)"]
    diffs = []
    if not live["description"]:
        diffs.append("GitHub description is empty")
    else:
        diffs.extend(stale_counts(entry, live["description"]))
        if wording and live["description"] != entry.get("description", "").strip():
            diffs.append(
                "description differs:\n"
                f"      registry: {entry.get('description', '')}\n"
                f"      github:   {live['description']}"
            )
    want_home = (entry.get("homepage") or "").rstrip("/")
    if want_home and live["homepage"].rstrip("/") != want_home:
        diffs.append(f"homepage differs: registry {want_home!r}, github {live['homepage']!r}")
    want_topics = sorted(entry.get("topics") or [])
    if not live["topics"]:
        diffs.append("GitHub topics are empty")
    else:
        missing = sorted(set(want_topics) - set(live["topics"]))
        if missing:
            diffs.append(f"topics in registry but not on GitHub: {', '.join(missing)}")
    return diffs


def check(
    entries: list[dict[str, Any]], fetch: Fetcher = fetch_repo, *, wording: bool = False
) -> dict[str, list[str]]:
    report = {}
    for entry in entries:
        if entry.get("status") in ("archived",):
            continue
        diffs = compare(entry, fetch(entry["repo"]), wording=wording)
        if diffs:
            report[entry["repo"]] = diffs
    return report


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--registry", type=Path, default=REPO_ROOT / "registry.json")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any repo drifts")
    parser.add_argument("--wording", action="store_true", help="also report description wording differences")
    args = parser.parse_args(argv)

    entries = json.loads(args.registry.read_text(encoding="utf-8"))
    report = check(entries, wording=args.wording)
    if args.json:
        print(json.dumps(report, indent=2))
    elif not report:
        print(f"All {len(entries)} repos match registry.json.")
    else:
        for repo, diffs in report.items():
            print(f"{repo}:")
            for d in diffs:
                print(f"  - {d}")
        print(f"\n{len(report)} of {len(entries)} repos differ from registry.json.")
    return 1 if (args.strict and report) else 0


if __name__ == "__main__":
    sys.exit(main())
