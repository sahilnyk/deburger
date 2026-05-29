"""Tests for the scanner."""

import asyncio
import pytest
from pathlib import Path
from deburger.scanner import FastScanner
from deburger.analyzers.base import IssueType


@pytest.fixture
def config():
    return {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
        "performance": {"max_workers": 4},
        "ignore": ["node_modules", "venv", "__pycache__"],
    }


@pytest.fixture
def scanner(config):
    return FastScanner(config)


def test_scan_single_file(scanner, tmp_path):
    code = "for item in items:\n    result = db.query(item.id)\n"
    test_file = tmp_path / "test.py"
    test_file.write_text(code)

    issues = asyncio.run(scanner.scan_path(str(test_file), incremental=False))
    assert len(issues) >= 1
    assert issues[0].type == IssueType.N_PLUS_ONE_QUERY


def test_scan_clean_file(scanner, tmp_path):
    code = "def add(a, b):\n    return a + b\n"
    test_file = tmp_path / "clean.py"
    test_file.write_text(code)

    issues = asyncio.run(scanner.scan_path(str(test_file), incremental=False))
    assert len(issues) == 0


def test_scan_directory(scanner, tmp_path):
    (tmp_path / "good.py").write_text("x = 1\n")
    (tmp_path / "bad.py").write_text("for i in items:\n    db.query(i.id)\n")

    issues = asyncio.run(scanner.scan_path(str(tmp_path), incremental=False))
    assert len(issues) >= 1


def test_scan_ignores_patterns(config, tmp_path):
    config["ignore"] = ["skip_this"]
    scanner = FastScanner(config)

    (tmp_path / "skip_this").mkdir()
    (tmp_path / "skip_this" / "bad.py").write_text("for i in x:\n    db.query(i)\n")

    issues = asyncio.run(scanner.scan_path(str(tmp_path), incremental=False))
    assert len(issues) == 0


def test_scan_nonexistent_path(scanner):
    issues = asyncio.run(scanner.scan_path("/nonexistent/path", incremental=False))
    assert issues == []
