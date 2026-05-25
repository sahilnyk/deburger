"""Tests for Python analyzer."""

import pytest
from decimal import Decimal
from deburger.analyzers.python_analyzer import PythonAnalyzer
from deburger.analyzers.base import IssueType, Severity


@pytest.fixture
def analyzer():
    return PythonAnalyzer()


@pytest.fixture
def config():
    return {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
    }


def test_detect_n_plus_one(analyzer, config):
    code = """
for item in items:
    result = db.query(item.id)
    process(result)
"""
    issues = analyzer.analyze("test.py", code, config)
    n_plus_one = [i for i in issues if i.type == IssueType.N_PLUS_ONE_QUERY]
    assert len(n_plus_one) == 1
    assert n_plus_one[0].severity == Severity.CRITICAL
    assert n_plus_one[0].estimated_monthly_cost > 0


def test_no_false_positive_without_db_call(analyzer, config):
    code = """
for item in items:
    result = process(item)
    print(result)
"""
    issues = analyzer.analyze("test.py", code, config)
    n_plus_one = [i for i in issues if i.type == IssueType.N_PLUS_ONE_QUERY]
    assert len(n_plus_one) == 0


def test_detect_sequential_async(analyzer, config):
    code = """
async def fetch_data():
    a = await get_users()
    b = await get_orders()
    c = await get_products()
    return a, b, c
"""
    issues = analyzer.analyze("test.py", code, config)
    seq = [i for i in issues if i.type == IssueType.SEQUENTIAL_ASYNC]
    assert len(seq) == 1
    assert seq[0].severity == Severity.HIGH
    assert "3" in seq[0].description


def test_no_false_positive_single_await(analyzer, config):
    code = """
async def fetch_data():
    a = await get_users()
    return a
"""
    issues = analyzer.analyze("test.py", code, config)
    seq = [i for i in issues if i.type == IssueType.SEQUENTIAL_ASYNC]
    assert len(seq) == 0


def test_syntax_error_returns_empty(analyzer, config):
    code = "def broken(\n    pass"
    issues = analyzer.analyze("test.py", code, config)
    assert issues == []


def test_supported_languages(analyzer):
    assert ".py" in analyzer.supported_languages
    assert analyzer.can_analyze("foo.py")
    assert not analyzer.can_analyze("foo.js")
