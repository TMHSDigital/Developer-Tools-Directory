"""Enforce that the shared design tokens stay reconciled across the two
presentation surfaces (finding C2).

site-template/tokens.css is the single source of truth for the shared,
non-themeable design tokens. The tool-site template embeds it with a Jinja
include; the catalog (docs/index.html) is a static, build-less file and so
mirrors the same declarations in its inline :root. This test parses tokens.css
and asserts both surfaces agree, so the drift the audit found (different type
scale, hover colors, and missing variables) cannot return silently.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS = REPO_ROOT / "site-template" / "tokens.css"
TEMPLATE = REPO_ROOT / "site-template" / "template.html.j2"
CATALOG = REPO_ROOT / "docs" / "index.html"


def _token_pairs() -> dict[str, str]:
    text = TOKENS.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{(.*?)\}", text, re.DOTALL)
    assert root, "tokens.css has no :root block"
    return {
        name: value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))
    }


def _strip_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


def test_tokens_file_has_expected_shared_tokens():
    pairs = _token_pairs()
    for expected in ("--text-muted", "--radius", "--hero-h1", "--stat-size", "--link-hover"):
        assert expected in pairs, f"tokens.css is missing {expected}"


def test_template_includes_tokens():
    assert "{% include 'tokens.css' %}" in TEMPLATE.read_text(encoding="utf-8"), (
        "template.html.j2 must embed the shared tokens via a Jinja include"
    )


def test_catalog_mirrors_tokens():
    catalog = _strip_ws(CATALOG.read_text(encoding="utf-8"))
    missing = []
    for name, value in _token_pairs().items():
        decl = _strip_ws(f"{name}:{value};")
        if decl not in catalog:
            missing.append(f"{name}: {value}")
    assert not missing, (
        "docs/index.html :root is out of sync with tokens.css for: "
        + ", ".join(missing)
    )
