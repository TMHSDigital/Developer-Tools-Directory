import io
import json
import sys
from pathlib import Path

import pytest

from scripts.drift_check import cli
from tests.conftest import FIXTURES, REPO_ROOT


def test_missing_local_returns_2(capsys):
    rc = cli.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--local" in err


def test_bad_path_returns_2(capsys, tmp_path: Path):
    rc = cli.main(["--local", str(tmp_path / "nope")])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


def test_clean_repo_exit_zero(capsys):
    rc = cli.main(["--local", str(FIXTURES / "clean_repo"), "--config", "nonexistent.json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "0 errors, 0 warnings" in out


def test_drifted_repo_exit_one(capsys):
    rc = cli.main(["--local", str(FIXTURES / "drifted_repo"), "--config", "nonexistent.json"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Summary:" in out


def test_broken_repo_exit_one(capsys):
    rc = cli.main(["--local", str(FIXTURES / "broken_repo"), "--config", "nonexistent.json"])
    assert rc == 1


def test_ignored_repo_exit_zero_infos_suppressed(capsys):
    rc = cli.main(["--local", str(FIXTURES / "ignored_repo"), "--config", "nonexistent.json"])
    assert rc == 0


def test_json_format(capsys):
    rc = cli.main([
        "--local", str(FIXTURES / "drifted_repo"),
        "--format", "json",
        "--config", "nonexistent.json",
    ])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert "summary" in payload
    assert "meta_version" in payload


def test_output_to_file(tmp_path: Path):
    out = tmp_path / "report.md"
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--output", str(out),
        "--config", "nonexistent.json",
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "Meta-repo version:" in text


def test_malformed_config_returns_2(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--config", str(bad),
    ])
    assert rc == 2
    assert "malformed JSON" in capsys.readouterr().err


def test_multiple_local_paths(capsys):
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--local", str(FIXTURES / "drifted_repo"),
        "--config", "nonexistent.json",
    ])
    assert rc == 1
    out = capsys.readouterr().out
    assert "clean_repo" in out
    assert "drifted_repo" in out


def test_verbose_flag_shows_infos(capsys):
    rc = cli.main([
        "--local", str(FIXTURES / "drifted_repo"),
        "--verbose",
        "--config", "nonexistent.json",
    ])
    assert rc == 1
    out = capsys.readouterr().out
    assert "infos" in out
