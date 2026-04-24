"""CLI entrypoint. Implements the exit-code contract from the Phase 2
acceptance criteria:

    0 - no drift (no errors, no warnings)
    1 - drift found (at least one error OR warning)
    2 - tool error (config malformed, repo path missing, etc.)

Invocation::

    python scripts/drift_check/cli.py --local E:\\CFX-Developer-Tools
    python scripts/drift_check/cli.py --local <path> --format json
    python scripts/drift_check/cli.py --local <path> --fix

``--fix`` delegates to the already-validated Phase 1 scripts under
``E:\\.TMHS-Tool-Ecosystem-Workspace\\phase1-script`` (discoverable via
``--fix-scripts`` for tests / alternate hosts). No git operations, no PRs.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

# Allow both `python -m scripts.drift_check.cli` and
# `python scripts/drift_check/cli.py` invocations.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from drift_check.checks import VersionSignalCheck  # type: ignore
    from drift_check.config import ConfigError, load_config  # type: ignore
    from drift_check.report import json_out, markdown  # type: ignore
    from drift_check.semver import parse_version  # type: ignore
    from drift_check.signals import _classify_by_name  # type: ignore
    from drift_check.snapshot import build_local_snapshot  # type: ignore
    from drift_check.types import Finding, RepoSnapshot, Version  # type: ignore
else:
    from .checks import VersionSignalCheck
    from .config import ConfigError, load_config
    from .report import json_out, markdown
    from .semver import parse_version
    from .signals import _classify_by_name
    from .snapshot import build_local_snapshot
    from .types import Finding, RepoSnapshot, Version


DEFAULT_PHASE1_SCRIPTS = Path(r"E:\.TMHS-Tool-Ecosystem-Workspace\phase1-script")


def _find_repo_root() -> Path:
    """Walk up from this file to the repo that contains ``VERSION``."""
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file():
            return candidate
    return here.parents[2]


def _read_meta_version(repo_root: Path) -> Version:
    raw = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    v = parse_version(raw)
    if v is None:
        raise SystemExit(f"meta-repo VERSION is not a valid semver: {raw!r}")
    return v


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="drift_check",
        description="Agent-file drift checker (Phase 2 Session A)",
    )
    p.add_argument(
        "--local",
        action="append",
        default=[],
        metavar="PATH",
        help="path to a local clone to check (repeatable)",
    )
    p.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="output format (default: markdown)",
    )
    p.add_argument(
        "--output",
        default="-",
        help="output path, or '-' for stdout (default: -)",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="include info-level findings in the report",
    )
    p.add_argument(
        "--fix",
        action="store_true",
        help="attempt in-place repair using Phase 1 scripts (local only)",
    )
    p.add_argument(
        "--fix-scripts",
        type=Path,
        default=DEFAULT_PHASE1_SCRIPTS,
        help="directory containing add_frontmatter.py / add_comment_marker.py",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="path to drift-checker.config.json (defaults to standards/drift-checker.config.json)",
    )
    p.add_argument(
        "--meta-commit",
        default="HEAD",
        help="meta-repo commit SHA for the snapshot record (default: HEAD)",
    )
    return p


def _build_snapshots(
    local_paths: Sequence[Path],
    meta_version: Version,
    meta_commit: str,
    config_path: Optional[Path],
) -> List[RepoSnapshot]:
    try:
        cfg = load_config(config_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    snapshots: List[RepoSnapshot] = []
    for path in local_paths:
        if not path.is_dir():
            print(f"error: --local path is not a directory: {path}", file=sys.stderr)
            raise SystemExit(2)
        snapshots.append(
            build_local_snapshot(
                repo_path=path,
                meta_version=meta_version,
                meta_commit=meta_commit,
                config=cfg,
            )
        )
    return snapshots


def _run_checks(snapshots: Sequence[RepoSnapshot]) -> List[Finding]:
    findings: List[Finding] = []
    for snap in snapshots:
        for check in (VersionSignalCheck(),):
            findings.extend(check.run(snap))
    return findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.local:
        print("error: at least one --local <path> is required", file=sys.stderr)
        return 2

    local_paths = [Path(p).resolve() for p in args.local]

    repo_root = _find_repo_root()
    try:
        meta_version = _read_meta_version(repo_root)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: cannot read VERSION: {exc}", file=sys.stderr)
        return 2

    try:
        snapshots = _build_snapshots(
            local_paths=local_paths,
            meta_version=meta_version,
            meta_commit=args.meta_commit,
            config_path=args.config,
        )
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 2

    findings = _run_checks(snapshots)

    if args.fix:
        touched = _apply_fixes_live(
            snapshots=snapshots,
            local_paths=local_paths,
            findings=findings,
            scripts_dir=args.fix_scripts,
            meta_version=meta_version,
        )
        if touched:
            # Rebuild snapshots & re-run checks so the report reflects the
            # post-fix state.
            try:
                snapshots = _build_snapshots(
                    local_paths=local_paths,
                    meta_version=meta_version,
                    meta_commit=args.meta_commit,
                    config_path=args.config,
                )
            except SystemExit as exc:
                return int(exc.code) if exc.code is not None else 2
            findings = _run_checks(snapshots)

    out_text = _render(snapshots, findings, args.format, args.verbose)

    if args.output == "-":
        sys.stdout.write(out_text)
    else:
        Path(args.output).write_text(out_text, encoding="utf-8")

    return _exit_code(findings)


def _render(
    snapshots: Sequence[RepoSnapshot],
    findings: Sequence[Finding],
    fmt: str,
    verbose: bool,
) -> str:
    if fmt == "json":
        return json_out.render(snapshots, findings, verbose=verbose)
    return markdown.render(snapshots, findings, verbose=verbose)


def _exit_code(findings: Sequence[Finding]) -> int:
    for f in findings:
        if f.severity in ("error", "warn"):
            return 1
    return 0


def _apply_fixes_live(
    snapshots: Sequence[RepoSnapshot],
    local_paths: Sequence[Path],
    findings: Sequence[Finding],
    scripts_dir: Path,
    meta_version: Version,
) -> int:
    """Run the Phase 1 scripts against each fixable Finding.

    Fixable = ``version-signal`` error findings (missing or malformed
    signal, or MAJOR.MINOR/patch drift). Pragma-skipped and tool_newer
    findings are left alone — those require human review.
    """
    fm = scripts_dir / "add_frontmatter.py"
    cm = scripts_dir / "add_comment_marker.py"
    if not fm.is_file() or not cm.is_file():
        print(
            f"error: --fix requires Phase 1 scripts in {scripts_dir}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    slug_to_root: dict[str, Path] = {}
    for path, snap in zip(local_paths, snapshots):
        slug_to_root[snap.slug] = path

    touched = 0
    for f in findings:
        if f.check != "version-signal":
            continue
        if f.severity not in ("error", "warn", "info"):
            continue
        if f.file is None:
            continue
        if f.severity == "info":
            # Could be patch_differs or pragma-skip. Only patch_differs is
            # fixable; pragma-skip messages start with "skipped".
            if f.message.startswith("skipped"):
                continue
        if f.severity == "warn":
            # tool_newer: a human should look. Skip.
            continue

        root = slug_to_root.get(f.repo)
        if root is None:
            continue
        abs_path = root / f.file
        fmt = _classify_by_name(f.file)
        script = fm if fmt == "yaml-frontmatter" else cm
        result = subprocess.run(
            [sys.executable, str(script), str(abs_path), str(meta_version)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            touched += 1
        else:
            print(
                f"warning: fix failed for {abs_path}: {result.stderr.strip()}",
                file=sys.stderr,
            )
    return touched


if __name__ == "__main__":
    sys.exit(main())
