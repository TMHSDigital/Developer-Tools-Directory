"""Tests for scripts/validate_registry.py."""
from __future__ import annotations

import copy
import json

import pytest

from scripts import validate_registry as vr
from tests.conftest import REPO_ROOT


def _real() -> list[dict]:
    return json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))


def _entry(**overrides) -> dict:
    base = {
        "name": "Sample",
        "repo": "TMHSDigital/Sample",
        "slug": "sample",
        "description": "d",
        "type": "cursor-plugin",
        "homepage": "https://tmhsdigital.github.io/Sample/",
        "skills": 1,
        "rules": 1,
        "mcpTools": 0,
        "extras": {},
        "topics": ["x"],
        "status": "active",
        "language": "Python",
        "license": "CC-BY-NC-ND-4.0",
        "pagesType": "static",
        "hasCI": True,
    }
    base.update(overrides)
    return base


def test_real_registry_is_valid():
    assert vr.validate(_real()) == []


def test_duplicate_slug_and_repo_rejected():
    errors = vr.validate([_entry(), _entry(name="Other")])
    assert any("duplicate slug" in e for e in errors)
    assert any("duplicate repo" in e for e in errors)


def test_homepage_required_when_pages_published():
    errors = vr.validate([_entry(homepage="")])
    assert any("homepage is required" in e for e in errors)
    assert vr.validate([_entry(homepage="", pagesType="none")]) == []


def test_npm_scope_enforced():
    errors = vr.validate([_entry(type="mcp-server", npm="@tmhsdigital/sample")])
    assert any("@tmhs/" in e for e in errors)


def test_unpublished_experimental_server_may_omit_npm():
    assert vr.validate([_entry(type="mcp-server", status="experimental")]) == []
    errors = vr.validate([_entry(type="mcp-server", status="active")])
    assert any("non-empty npm" in e for e in errors)


@pytest.mark.parametrize("field", ["skills", "rules", "mcpTools"])
def test_negative_and_bool_counts_rejected(field):
    assert vr.validate([_entry(**{field: -1})])
    assert vr.validate([_entry(**{field: True})])


def test_every_real_entry_has_a_known_category():
    """Each tool must land under a catalog filter chip (DTD#115)."""
    missing = [e["slug"] for e in _real() if e.get("category") not in vr.CATEGORIES]
    assert not missing, missing


def test_unknown_category_rejected():
    assert any("category" in e for e in vr.validate([_entry(category="nope")]))


def test_unknown_license_rejected():
    assert any("license" in e for e in vr.validate([_entry(license="GPL-3.0")]))


def test_missing_field_reported():
    entry = _entry()
    del entry["status"]
    assert any("missing required field 'status'" in e for e in vr.validate([entry]))


def test_main_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps([_entry()]), encoding="utf-8")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([_entry(), copy.deepcopy(_entry())]), encoding="utf-8")
    assert vr.main(["x", str(good)]) == 0
    assert vr.main(["x", str(bad)]) == 1
