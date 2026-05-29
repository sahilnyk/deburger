"""Tests for edge cases."""

import asyncio
import pytest
from deburger.scanner import FastScanner
from deburger.analyzers.python_analyzer import PythonAnalyzer
from deburger.analyzers.javascript_analyzer import JavaScriptAnalyzer


@pytest.fixture
def config():
    return {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
        "performance": {"max_workers": 2},
        "ignore": ["node_modules", "__pycache__"],
    }


def test_empty_file(config):
    analyzer = PythonAnalyzer()
    issues = analyzer.analyze("empty.py", "", config)
    assert issues == []


def test_whitespace_only_file(config):
    analyzer = PythonAnalyzer()
    issues = analyzer.analyze("blank.py", "   \n\n   \n", config)
    assert issues == []


def test_binary_content_no_crash(config):
    analyzer = PythonAnalyzer()
    issues = analyzer.analyze("weird.py", "\x00\x01\x02\x03", config)
    assert isinstance(issues, list)


def test_huge_single_line(config):
    analyzer = PythonAnalyzer()
    code = "x = " + "1 + " * 10000 + "1\n"
    issues = analyzer.analyze("big.py", code, config)
    assert isinstance(issues, list)


def test_js_empty_file(config):
    analyzer = JavaScriptAnalyzer()
    issues = analyzer.analyze("empty.js", "", config)
    assert issues == []


def test_scan_empty_directory(config, tmp_path):
    scanner = FastScanner(config)
    issues = asyncio.run(scanner.scan_path(str(tmp_path), incremental=False))
    assert issues == []


def test_scan_unsupported_extension(config, tmp_path):
    (tmp_path / "data.csv").write_text("a,b,c\n1,2,3\n")
    scanner = FastScanner(config)
    issues = asyncio.run(scanner.scan_path(str(tmp_path), incremental=False))
    assert issues == []


def test_scan_file_with_encoding_error(config, tmp_path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_bytes(b"\xff\xfe" + "for x in y:\n    db.query(x)\n".encode("utf-16-le"))
    scanner = FastScanner(config)
    issues = asyncio.run(scanner.scan_path(str(tmp_path), incremental=False))
    assert isinstance(issues, list)
