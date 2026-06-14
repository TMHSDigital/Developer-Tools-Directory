#!/usr/bin/env python3
"""Canonical scaffold-generation library for TMHSDigital developer tool repos.

This module holds the single, importable implementation of repo generation so
both the ``create-tool.py`` CLI and any second generator (e.g. the
Developer-Tools-MCP ``createTool`` path) can DELEGATE to one code path instead
of reimplementing it and drifting apart.

Public entrypoints:

* ``generate_repo(...)`` - render a complete repo of a given type into an
  output directory and (by default) register it in the meta catalog.
* ``build_registry_entry(...)`` - build a schema-valid ``registry.json`` entry
  for a generated repo.
* ``register_in_registry(...)`` - append an entry to a registry and regenerate
  the derived artifacts via ``sync_from_registry.sync_all`` (one sync path).

The born-green acceptance contract these must satisfy is documented in
``standards/born-green-contract.md``.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:  # pragma: no cover - environment guard
    raise SystemExit("Error: Jinja2 is required. Install it with: pip install Jinja2")


SCAFFOLD_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCAFFOLD_DIR / "templates"
META_ROOT = SCAFFOLD_DIR.parent
STANDARDS_VERSION_FILE = META_ROOT / "STANDARDS_VERSION"
VERSION_FILE = META_ROOT / "VERSION"

LICENSE_FILES = {
    "cc-by-nc-nd-4.0": "CC-BY-NC-ND-4.0",
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
}

SPDX = dict(LICENSE_FILES)

DEFAULT_AUTHOR_NAME = "TMHSDigital"
DEFAULT_AUTHOR_EMAIL = "contact@users.noreply.github.com"
REPO_OWNER = "TMHSDigital"


class ScaffoldError(Exception):
    """Raised for any unrecoverable generation/registration error.

    The CLI catches this and exits non-zero; library callers handle it.
    """


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _read_semver(path: Path, purpose: str) -> str:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ScaffoldError(
            f"{path.name} not found at {path}. The scaffold must run from a "
            f"working copy of Developer-Tools-Directory."
        ) from exc
    except OSError as exc:
        raise ScaffoldError(f"could not read {path}: {exc}") from exc
    if not re.fullmatch(r"\d+\.\d+\.\d+", raw):
        raise ScaffoldError(
            f"{path.name} contents {raw!r} are not a valid X.Y.Z semver string; "
            f"refusing to {purpose} from a malformed value."
        )
    return raw


def read_standards_version() -> str:
    """Read meta STANDARDS_VERSION. New repos are pre-aligned with it."""
    return _read_semver(STANDARDS_VERSION_FILE, "emit a standards-version marker")


def read_meta_version() -> tuple[int, int, int]:
    """Read meta VERSION as (major, minor, patch). Action pins derive from it."""
    raw = _read_semver(VERSION_FILE, "derive workflow action pins")
    major, minor, patch = (int(x) for x in raw.split("."))
    return major, minor, patch


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )


def render_template(env: Environment, template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)


def write_file(base: Path, rel_path: str, content: str, *, verbose: bool = True) -> None:
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    if verbose:
        print(f"  created {rel_path}")


def build_context(
    *,
    name: str,
    slug: str,
    description: str,
    repo_type: str,
    has_mcp: bool,
    skill_names: list[str],
    rule_names: list[str],
    license_key: str,
    author_name: str,
    author_email: str,
) -> dict[str, Any]:
    standards_version = read_standards_version()
    meta_major, meta_minor, meta_patch = read_meta_version()
    return {
        "name": name,
        "slug": slug,
        "description": description,
        "type": repo_type,
        "has_mcp": has_mcp,
        "skills": skill_names,
        "rules": rule_names,
        "skill_count": len(skill_names),
        "rule_count": len(rule_names),
        "license_spdx": SPDX[license_key],
        "license_key": license_key,
        "author_name": author_name,
        "author_email": author_email,
        "repo_owner": REPO_OWNER,
        "repo_name": slug,
        "standards_version": standards_version,
        "meta_major": meta_major,
        "meta_minor": meta_minor,
        "meta_patch": meta_patch,
        "meta_version": f"{meta_major}.{meta_minor}.{meta_patch}",
        "year": datetime.datetime.now(datetime.timezone.utc).year,
    }


def _skill_content(skill: str, standards_version: str) -> str:
    title = skill.replace("-", " ").title()
    return (
        f"---\nname: {skill}\n"
        "description: TODO - describe this skill\n"
        'globs: ["**/*"]\n'
        "alwaysApply: false\n"
        f"standards-version: {standards_version}\n"
        f"---\n\n# {title}\n\nTODO: Add skill content here.\n"
    )


def _rule_content(rule: str, standards_version: str) -> str:
    title = rule.replace("-", " ").title()
    return (
        "---\ndescription: TODO - describe this rule\n"
        'globs: ["**/*"]\n'
        "alwaysApply: false\n"
        f"standards-version: {standards_version}\n"
        f"---\n\n# {title}\n\nTODO: Add rule content here.\n"
    )


def _render_repo(output_dir: Path, ctx: dict, *, verbose: bool) -> None:
    env = _env()
    repo_type = ctx["type"]
    has_mcp = ctx["has_mcp"]

    if repo_type == "cursor-plugin":
        write_file(output_dir, ".cursor-plugin/plugin.json", render_template(env, "plugin.json.j2", ctx), verbose=verbose)

    # Workflows: type-specific set matching standards/drift-checker.config.json
    # plus the two optional-for-both workflows (pages, label-sync). mcp-server
    # repos do NOT get cursor-plugin-specific validate.yml / release.yml.
    if repo_type == "mcp-server":
        write_file(output_dir, ".github/workflows/publish.yml", render_template(env, "publish.yml.j2", ctx), verbose=verbose)
        write_file(output_dir, ".github/workflows/ci.yml", render_template(env, "ci.yml.j2", ctx), verbose=verbose)
        write_file(output_dir, ".github/workflows/release.yml", render_template(env, "release.mcp.yml.j2", ctx), verbose=verbose)
        write_file(output_dir, ".github/workflows/pages.yml", render_template(env, "pages.mcp.yml.j2", ctx), verbose=verbose)
    else:
        write_file(output_dir, ".github/workflows/validate.yml", render_template(env, "validate.yml.j2", ctx), verbose=verbose)
        write_file(output_dir, ".github/workflows/release.yml", render_template(env, "release.yml.j2", ctx), verbose=verbose)
        write_file(output_dir, ".github/workflows/pages.yml", render_template(env, "pages.yml.j2", ctx), verbose=verbose)
    write_file(output_dir, ".github/workflows/stale.yml", render_template(env, "stale.yml.j2", ctx), verbose=verbose)
    write_file(output_dir, ".github/workflows/drift-check.yml", render_template(env, "drift-check.yml.j2", ctx), verbose=verbose)
    write_file(output_dir, ".github/workflows/label-sync.yml", render_template(env, "label-sync.yml.j2", ctx), verbose=verbose)

    write_file(output_dir, ".github/dependabot.yml", render_template(env, "dependabot.yml.j2", ctx), verbose=verbose)

    for rel, tmpl in (
        ("README.md", "README.md.j2"),
        ("AGENTS.md", "AGENTS.md.j2"),
        ("CLAUDE.md", "CLAUDE.md.j2"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md.j2"),
        ("CHANGELOG.md", "CHANGELOG.md.j2"),
        ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.md.j2"),
        ("SECURITY.md", "SECURITY.md.j2"),
        ("ROADMAP.md", "ROADMAP.md.j2"),
        ("LICENSE", "LICENSE.j2"),
        (".cursorrules", "cursorrules.j2"),
        (".gitignore", "gitignore.j2"),
        ("site.json", "site.json.j2"),
        ("mcp-tools.json", "mcp-tools.json.j2"),
    ):
        write_file(output_dir, rel, render_template(env, tmpl, ctx), verbose=verbose)

    (output_dir / "assets").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets" / ".gitkeep").touch()

    if repo_type == "mcp-server":
        write_file(output_dir, "package.json", render_template(env, "package.json.j2", ctx), verbose=verbose)
        write_file(output_dir, "docs/index.html", render_template(env, "docs/index.mcp.html.j2", ctx), verbose=verbose)

    standards_version = ctx["standards_version"]
    for skill in ctx["skills"]:
        write_file(output_dir, f"skills/{skill}/SKILL.md", _skill_content(skill, standards_version), verbose=verbose)
    for rule in ctx["rules"]:
        write_file(output_dir, f"rules/{rule}.mdc", _rule_content(rule, standards_version), verbose=verbose)

    (output_dir / "tests").mkdir(parents=True, exist_ok=True)
    (output_dir / "tests" / ".gitkeep").touch()

    if has_mcp:
        write_file(output_dir, "mcp-server/server.py", render_template(env, "mcp-server/server.py.j2", ctx), verbose=verbose)
        write_file(output_dir, "mcp-server/requirements.txt", render_template(env, "mcp-server/requirements.txt.j2", ctx), verbose=verbose)
        (output_dir / "mcp-server" / "tools").mkdir(parents=True, exist_ok=True)
        (output_dir / "mcp-server" / "tools" / ".gitkeep").touch()
        (output_dir / "mcp-server" / "data").mkdir(parents=True, exist_ok=True)
        (output_dir / "mcp-server" / "data" / ".gitkeep").touch()
        write_file(output_dir, ".cursor/mcp.json", render_template(env, "mcp-server/mcp.json.j2", ctx), verbose=verbose)


def _resolve_repo_type(output_dir: Path, intended: str) -> str:
    """Resolve the repo type from the generated tree using the SAME positive
    marker detector the drift checker uses, so the registry entry's type
    matches what CI will see. Falls back to ``intended`` if the detector
    cannot be imported (e.g. delegated generator without scripts/ on path)."""
    try:
        if str(META_ROOT) not in sys.path:
            sys.path.insert(0, str(META_ROOT))
        from scripts.drift_check.snapshot import _detect_repo_type  # type: ignore
    except Exception:
        return intended
    detected = _detect_repo_type(output_dir)
    if detected == "unknown":
        raise ScaffoldError(
            f"generated repo at {output_dir} classifies as 'unknown'; the "
            f"positive type marker for {intended!r} was not written. This is a "
            f"born-unknown bug - see standards/born-green-contract.md."
        )
    return detected


def build_registry_entry(
    *,
    name: str,
    slug: str,
    description: str,
    repo_type: str,
    skill_count: int,
    rule_count: int,
    license_key: str,
) -> dict[str, Any]:
    """Build a schema-valid registry.json entry for a generated repo.

    Mirrors the schema enforced by validate.yml. Intentionally has NO
    ``version`` field (removed in PR #73). Counts reflect generated content;
    a fresh repo has no MCP tools yet so ``mcpTools`` is 0.
    """
    homepage = f"https://{REPO_OWNER.lower()}.github.io/{slug}/"
    return {
        "name": name,
        "repo": f"{REPO_OWNER}/{slug}",
        "slug": slug,
        "description": description,
        "type": repo_type,
        "homepage": homepage,
        "skills": skill_count,
        "rules": rule_count,
        "mcpTools": 0,
        "extras": {},
        "topics": [repo_type, "developer-tools"],
        "status": "active",
        "language": "TypeScript" if repo_type == "mcp-server" else "Python",
        "license": SPDX[license_key],
        "pagesType": "static",
        "hasCI": True,
    }


def register_in_registry(
    registry_root: Path,
    entry: dict[str, Any],
    *,
    run_sync: bool = True,
    verbose: bool = True,
) -> None:
    """Append ``entry`` to ``registry_root/registry.json`` and regenerate the
    derived artifacts via the shared ``sync_all`` code path.

    Refuses to register a slug or repo that already exists (idempotency
    guard: a re-run must not silently duplicate or clobber a catalog entry).
    """
    registry_path = registry_root / "registry.json"
    if not registry_path.is_file():
        raise ScaffoldError(f"registry.json not found at {registry_path}")
    try:
        entries = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScaffoldError(f"registry.json is not valid JSON: {exc}") from exc
    if not isinstance(entries, list):
        raise ScaffoldError("registry.json must be a JSON array")

    for existing in entries:
        if existing.get("slug") == entry["slug"]:
            raise ScaffoldError(
                f"registry already contains slug {entry['slug']!r}; refusing to "
                f"duplicate. Use --no-register or remove the existing entry."
            )
        if existing.get("repo") == entry["repo"]:
            raise ScaffoldError(
                f"registry already contains repo {entry['repo']!r}; refusing to "
                f"duplicate."
            )

    entries.append(entry)
    registry_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if verbose:
        print(f"  registered {entry['slug']} in {registry_path}")

    if run_sync:
        if str(META_ROOT) not in sys.path:
            sys.path.insert(0, str(META_ROOT))
        from scripts.sync_from_registry import sync_all  # type: ignore

        sync_all(registry_root, check=False)
        if verbose:
            print("  regenerated derived artifacts (README, CLAUDE, docs)")


def generate_repo(
    *,
    name: str,
    description: str,
    slug: Optional[str] = None,
    repo_type: str = "cursor-plugin",
    mcp_server: bool = False,
    skills: int = 0,
    rules: int = 0,
    license_key: str = "cc-by-nc-nd-4.0",
    output: str = "output",
    author_name: str = DEFAULT_AUTHOR_NAME,
    author_email: str = DEFAULT_AUTHOR_EMAIL,
    register: bool = True,
    registry_root: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    """Render a complete, standards-compliant repo and (by default) register
    it in the meta catalog. Returns the path to the generated repo.

    Setting ``register=False`` skips catalog registration (the rare
    deliberate case). ``registry_root`` overrides where registration writes
    (defaults to the meta-repo root); used by tests to target a temp catalog.
    """
    if repo_type not in ("cursor-plugin", "mcp-server"):
        raise ScaffoldError(f"unknown repo type: {repo_type!r}")
    if license_key not in LICENSE_FILES:
        raise ScaffoldError(f"unknown license: {license_key!r}")

    slug = slug or slugify(name)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        raise ScaffoldError(f"slug {slug!r} is not valid kebab-case")

    output_dir = Path(output) / slug
    if output_dir.exists():
        raise ScaffoldError(f"output directory already exists: {output_dir}")

    skill_names = [f"skill-{i + 1}" for i in range(skills)]
    rule_names = [f"rule-{i + 1}" for i in range(rules)]

    ctx = build_context(
        name=name,
        slug=slug,
        description=description,
        repo_type=repo_type,
        has_mcp=mcp_server,
        skill_names=skill_names,
        rule_names=rule_names,
        license_key=license_key,
        author_name=author_name,
        author_email=author_email,
    )

    if verbose:
        print(f"\nScaffolding '{name}' ({slug}) into {output_dir}\n")

    _render_repo(output_dir, ctx, verbose=verbose)

    # Resolve the type from the generated tree via the drift checker's
    # positive-marker detector; this both validates the marker was written
    # and pins the registry entry's type to what CI will detect.
    resolved_type = _resolve_repo_type(output_dir, repo_type)

    if register:
        root = registry_root if registry_root is not None else META_ROOT
        entry = build_registry_entry(
            name=name,
            slug=slug,
            description=description,
            repo_type=resolved_type,
            skill_count=len(skill_names),
            rule_count=len(rule_names),
            license_key=license_key,
        )
        register_in_registry(Path(root), entry, run_sync=True, verbose=verbose)

    return output_dir
