"""Tests for deburger:ignore suppression."""

import pytest
from deburger.analyzers.python_analyzer import PythonAnalyzer
from deburger.analyzers.base import IssueType


@pytest.fixture
def analyzer():
    return PythonAnalyzer()


@pytest.fixture
def config():
    return {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
    }


def test_inline_suppression(analyzer, config):
    code = "for item in items:  # deburger:ignore\n    result = db.query(item.id)\n"
    issues = analyzer.analyze("test.py", code, config)
    assert not any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)


def test_line_above_suppression(analyzer, config):
    code = "# deburger:ignore\nfor item in items:\n    result = db.query(item.id)\n"
    issues = analyzer.analyze("test.py", code, config)
    assert not any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)


def test_no_suppression_without_comment(analyzer, config):
    code = "for item in items:\n    result = db.query(item.id)\n"
    issues = analyzer.analyze("test.py", code, config)
    assert any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)
