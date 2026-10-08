#!/usr/bin/env python3
"""Schema and consistency validation for registry.json.

Runs in CI (validate.yml) and is importable by tests. Exits 1 and prints
GitHub ``::error::`` annotations when any entry is invalid.

Usage: python scripts/validate_registry.py [path/to/registry.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA: dict[str, type] = {
    "name": str,
    "repo": str,
    "slug": str,
    "description": str,
    "type": str,
    "homepage": str,
    "skills": int,
    "rules": int,
    "mcpTools": int,
    "extras": dict,
    "topics": list,
    "status": str,
    "language": str,
    "license": str,
    "pagesType": str,
    "hasCI": bool,
}
OPTIONAL: dict[str, type] = {"npm": str, "archetype": str, "category": str}
VALID_TYPES = {"cursor-plugin", "mcp-server"}
VALID_STATUS = {"experimental", "beta", "active", "maintenance", "deprecated", "archived"}
VALID_PAGES = {"static", "mkdocs", "none"}
VALID_ARCHETYPES = {"deployed-service"}
VALID_LICENSES = {"CC-BY-NC-ND-4.0", "CC-BY-NC-ND-4.0 AND MIT", "MIT", "Apache-2.0"}
NPM_SCOPE = "@tmhs/"
COUNT_FIELDS = ("skills", "rules", "mcpTools")


def validate(data: Any) -> list[str]:
    """Return a list of human-readable errors (empty when valid)."""
    if not isinstance(data, list):
        return ["registry.json must be an array"]

    errors: list[str] = []
    seen_slugs: dict[str, str] = {}
    seen_repos: dict[str, str] = {}

    for i, tool in enumerate(data):
        label = "Entry %d (%s)" % (i, tool.get("name", "?") if isinstance(tool, dict) else "?")
        if not isinstance(tool, dict):
            errors.append("%s: must be an object" % label)
            continue

        for field, expected in SCHEMA.items():
            if field not in tool:
                errors.append("%s: missing required field '%s'" % (label, field))
            elif not isinstance(tool[field], expected) or (
                expected is int and isinstance(tool[field], bool)
            ):
                errors.append(
                    "%s: '%s' must be %s, got %s"
                    % (label, field, expected.__name__, type(tool[field]).__name__)
                )
        for field, expected in OPTIONAL.items():
            if field in tool and not isinstance(tool[field], expected):
                errors.append("%s: optional '%s' must be %s" % (label, field, expected.__name__))

        for field in COUNT_FIELDS:
            value = tool.get(field)
            if isinstance(value, int) and not isinstance(value, bool) and value < 0:
                errors.append("%s: '%s' must be >= 0" % (label, field))

        if tool.get("type") not in VALID_TYPES:
            errors.append("%s: type must be one of %s" % (label, sorted(VALID_TYPES)))
        if tool.get("status") not in VALID_STATUS:
            errors.append("%s: status must be one of %s" % (label, sorted(VALID_STATUS)))
        if tool.get("pagesType") not in VALID_PAGES:
            errors.append("%s: pagesType must be one of %s" % (label, sorted(VALID_PAGES)))
        if tool.get("license") not in VALID_LICENSES:
            errors.append("%s: license must be one of %s" % (label, sorted(VALID_LICENSES)))

        topics = tool.get("topics", [])
        if isinstance(topics, list) and not all(isinstance(t, str) for t in topics):
            errors.append("%s: topics must be array of strings" % label)

        slug = tool.get("slug")
        if isinstance(slug, str):
            if slug in seen_slugs:
                errors.append("%s: duplicate slug '%s' (also %s)" % (label, slug, seen_slugs[slug]))
            seen_slugs[slug] = label
        repo = tool.get("repo")
        if isinstance(repo, str):
            key = repo.lower()
            if key in seen_repos:
                errors.append("%s: duplicate repo '%s' (also %s)" % (label, repo, seen_repos[key]))
            seen_repos[key] = label
            if repo.count("/") != 1:
                errors.append("%s: repo must be 'owner/name'" % label)

        homepage = tool.get("homepage")
        if tool.get("pagesType") in ("static", "mkdocs") and not homepage:
            errors.append("%s: homepage is required when pagesType is not 'none'" % label)
        if homepage and not str(homepage).startswith("https://"):
            errors.append("%s: homepage must be an https URL" % label)

        npm = tool.get("npm")
        if "npm" in tool and isinstance(npm, str) and not npm.startswith(NPM_SCOPE):
            errors.append("%s: npm package must use the %s scope" % (label, NPM_SCOPE))

        archetype = tool.get("archetype")
        if "archetype" in tool:
            if archetype not in VALID_ARCHETYPES:
                errors.append("%s: archetype must be one of %s" % (label, sorted(VALID_ARCHETYPES)))
            if tool.get("type") != "mcp-server":
                errors.append("%s: archetype is only valid for mcp-server entries" % label)
        if tool.get("type") == "mcp-server":
            if archetype == "deployed-service":
                if "npm" in tool:
                    errors.append("%s: deployed-service must omit npm" % label)
            elif not (isinstance(npm, str) and npm.strip()):
                # An experimental server may not be published yet; every
                # other npm-archetype server must name its package.
                if tool.get("status") != "experimental":
                    errors.append("%s: mcp-server entries must have a non-empty npm field" % label)

    return errors


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "registry.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("::error::cannot read %s: %s" % (path, exc), file=sys.stderr)
        return 1
    errors = validate(data)
    if errors:
        for e in errors:
            print("::error::" + e, file=sys.stderr)
        return 1
    print("Registry valid: %d tools" % len(data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
