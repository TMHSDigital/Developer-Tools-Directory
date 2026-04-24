import json
from pathlib import Path

import pytest

from scripts.drift_check import cli
from tests.conftest import FIXTURES


@pytest.fixture
def meta_repo(tmp_path: Path) -> Path:
    """Isolated meta-repo for CLI tests. Pins meta VERSION to 1.6.3 so that
    the on-disk fixtures (which still carry 1.6.3 signals) read as clean."""
    root = tmp_path / "meta"
    root.mkdir()
    (root / "VERSION").write_text("1.6.3", encoding="utf-8")
    (root / "standards").mkdir()
    (root / "standards" / "required-refs.json").write_text(
        '{"version": 1, "requirements": {"cursor-plugin": {}, "mcp-server": {}}}',
        encoding="utf-8",
    )
    return root


def _meta_args(meta_repo: Path) -> list[str]:
    return ["--meta-repo", str(meta_repo), "--config", "nonexistent.json"]


def test_missing_local_returns_2(capsys):
    rc = cli.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--local" in err


def test_bad_path_returns_2(capsys, tmp_path: Path, meta_repo: Path):
    rc = cli.main(["--local", str(tmp_path / "nope"), *_meta_args(meta_repo)])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


def test_clean_repo_exit_zero(capsys, meta_repo: Path):
    rc = cli.main(["--local", str(FIXTURES / "clean_repo"), *_meta_args(meta_repo)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "0 errors, 0 warnings" in out


def test_drifted_repo_exit_one(capsys, meta_repo: Path):
    rc = cli.main(["--local", str(FIXTURES / "drifted_repo"), *_meta_args(meta_repo)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Summary:" in out


def test_broken_repo_exit_one(capsys, meta_repo: Path):
    rc = cli.main(["--local", str(FIXTURES / "broken_repo"), *_meta_args(meta_repo)])
    assert rc == 1


def test_ignored_repo_exit_zero_infos_suppressed(capsys, meta_repo: Path):
    rc = cli.main(["--local", str(FIXTURES / "ignored_repo"), *_meta_args(meta_repo)])
    assert rc == 0


def test_json_format(capsys, meta_repo: Path):
    rc = cli.main([
        "--local", str(FIXTURES / "drifted_repo"),
        "--format", "json",
        *_meta_args(meta_repo),
    ])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert "summary" in payload
    assert "meta_version" in payload


def test_output_to_file(tmp_path: Path, meta_repo: Path):
    out = tmp_path / "report.md"
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--output", str(out),
        *_meta_args(meta_repo),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "Meta-repo version:" in text


def test_malformed_config_returns_2(tmp_path: Path, capsys, meta_repo: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--meta-repo", str(meta_repo),
        "--config", str(bad),
    ])
    assert rc == 2
    assert "malformed JSON" in capsys.readouterr().err


def test_multiple_local_paths(capsys, meta_repo: Path):
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--local", str(FIXTURES / "drifted_repo"),
        *_meta_args(meta_repo),
    ])
    assert rc == 1
    out = capsys.readouterr().out
    assert "clean_repo" in out
    assert "drifted_repo" in out


def test_verbose_flag_shows_infos(capsys, meta_repo: Path):
    rc = cli.main([
        "--local", str(FIXTURES / "drifted_repo"),
        "--verbose",
        *_meta_args(meta_repo),
    ])
    assert rc == 1
    out = capsys.readouterr().out
    assert "infos" in out


def test_gh_summary_requires_env(capsys, meta_repo: Path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--format", "gh-summary",
        *_meta_args(meta_repo),
    ])
    assert rc == 2
    assert "GITHUB_STEP_SUMMARY" in capsys.readouterr().err


def test_gh_summary_writes_file(tmp_path: Path, meta_repo: Path, monkeypatch):
    target = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(target))
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--format", "gh-summary",
        *_meta_args(meta_repo),
    ])
    assert rc == 0
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "Drift report" in text
    assert "clean" in text.lower()
