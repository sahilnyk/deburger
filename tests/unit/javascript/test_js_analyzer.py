"""Tests for JavaScript/TypeScript analyzer."""

import pytest
from deburger.analyzers.javascript_analyzer import JavaScriptAnalyzer
from deburger.analyzers.base import IssueType, Severity


@pytest.fixture
def analyzer():
    return JavaScriptAnalyzer()


@pytest.fixture
def config():
    return {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
    }


class TestNPlusOne:
    def test_detects_in_for_loop(self, analyzer, config):
        code = "for (const item of items) {\n    const r = await db.find(item.id);\n}\n"
        issues = analyzer.analyze("app.js", code, config)
        assert any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)

    def test_no_false_positive(self, analyzer, config):
        code = "for (const item of items) {\n    transform(item);\n}\n"
        issues = analyzer.analyze("app.js", code, config)
        assert not any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)


class TestSequentialAsync:
    def test_detects_sequential_awaits(self, analyzer, config):
        code = "async function f() {\n    const a = await getA();\n    const b = await getB();\n    const c = await getC();\n}\n"
        issues = analyzer.analyze("app.ts", code, config)
        seq = [i for i in issues if i.type == IssueType.SEQUENTIAL_ASYNC]
        assert len(seq) == 1
        assert "3" in seq[0].description

    def test_single_await_ok(self, analyzer, config):
        code = "async function f() {\n    const a = await getA();\n    return a;\n}\n"
        issues = analyzer.analyze("app.js", code, config)
        assert not any(i.type == IssueType.SEQUENTIAL_ASYNC for i in issues)


class TestSupported:
    def test_js_ts_jsx_tsx(self, analyzer):
        for ext in [".js", ".ts", ".jsx", ".tsx"]:
            assert analyzer.can_analyze(f"file{ext}")

    def test_rejects_py(self, analyzer):
        assert not analyzer.can_analyze("file.py")


class TestSuppression:
    def test_ignore_inline(self, analyzer, config):
        code = "for (const item of items) {\n    const r = await db.find(item.id); // deburger:ignore\n}\n"
        issues = analyzer.analyze("app.js", code, config)
        assert not any(i.type == IssueType.N_PLUS_ONE_QUERY for i in issues)
