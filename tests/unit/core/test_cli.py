"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from deburger.cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "deburger v" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "deburger v" in result.output


def test_check_clean_dir(tmp_path):
    (tmp_path / "clean.py").write_text("x = 1\n")
    result = runner.invoke(app, ["check", str(tmp_path), "--full"])
    assert result.exit_code == 0
    assert "no expensive patterns" in result.output


def test_check_finds_issues(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".deburger.yml").write_text("provider: aws\nregion: us-east-1\n")
    (tmp_path / "bad.py").write_text(
        "for item in items:\n    result = db.query(item.id)\n    process(result)\n"
    )
    result = runner.invoke(app, ["check", ".", "--full"])
    assert result.exit_code != 0 or "issues found" in result.output


def test_check_json_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".deburger.yml").write_text("provider: aws\nregion: us-east-1\n")
    (tmp_path / "bad.py").write_text(
        "for item in items:\n    result = db.query(item.id)\n    process(result)\n"
    )
    result = runner.invoke(app, ["check", ".", "--full", "--json"])
    assert '"issues"' in result.output or "issues found" in result.output


def test_init_creates_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".deburger.yml").exists()


def test_init_with_provider(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--provider", "gcp"])
    assert result.exit_code == 0
    assert "gcp" in (tmp_path / ".deburger.yml").read_text()


def test_init_skips_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".deburger.yml").write_text("provider: aws\n")
    result = runner.invoke(app, ["init"])
    assert "already exists" in result.output


def test_hook_no_args():
    result = runner.invoke(app, ["hook"])
    assert result.exit_code == 0
    assert "--install" in result.output


def test_no_args_shows_help():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "deburger" in result.output
