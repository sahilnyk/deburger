"""Tests for fix generation and application."""

import asyncio
import pytest
from decimal import Decimal
from deburger.optimizer import CodeFixer, Fix, FixApplier
from deburger.analyzers.base import Issue, IssueType, Severity


@pytest.fixture
def fixer():
    return CodeFixer()


@pytest.fixture
def n_plus_one_issue():
    return Issue(
        type=IssueType.N_PLUS_ONE_QUERY,
        severity=Severity.CRITICAL,
        file_path="app.py",
        line_number=1,
        code_snippet="for item in items:\n    result = db.query(item.id)",
        estimated_monthly_cost=Decimal("300"),
        description="N+1 query",
        explanation="N+1 in loop",
        savings_monthly=Decimal("285"),
    )


@pytest.fixture
def seq_async_issue():
    return Issue(
        type=IssueType.SEQUENTIAL_ASYNC,
        severity=Severity.HIGH,
        file_path="api.py",
        line_number=2,
        code_snippet="    a = await get_a()\n    b = await get_b()",
        estimated_monthly_cost=Decimal("50"),
        description="Sequential async",
        explanation="2 sequential awaits",
        savings_monthly=Decimal("45"),
    )


class TestCodeFixer:
    def test_generates_python_n_plus_one_fix(self, fixer, n_plus_one_issue):
        code = "for item in items:\n    result = db.query(item.id)\n    process(result)\n"
        fix = fixer.generate_fix(n_plus_one_issue, code)
        assert fix is not None
        assert "bulk" in fix.explanation
        assert fix.confidence > 0
        assert not fix.auto_apply_safe

    def test_generates_python_sequential_fix(self, fixer, seq_async_issue):
        code = "async def f():\n    a = await get_a()\n    b = await get_b()\n    return a, b\n"
        fix = fixer.generate_fix(seq_async_issue, code)
        assert fix is not None
        assert "asyncio.gather" in fix.fixed_code
        assert fix.auto_apply_safe

    def test_generates_js_sequential_fix(self, fixer):
        issue = Issue(
            type=IssueType.SEQUENTIAL_ASYNC,
            severity=Severity.HIGH,
            file_path="api.js",
            line_number=1,
            code_snippet="const a = await getA();\nconst b = await getB();",
            estimated_monthly_cost=Decimal("50"),
            description="Sequential async",
            explanation="2 sequential awaits",
            savings_monthly=Decimal("45"),
        )
        code = "const a = await getA();\nconst b = await getB();\n"
        fix = fixer.generate_fix(issue, code)
        assert fix is not None
        assert "Promise.all" in fix.fixed_code

    def test_returns_none_for_unknown_type(self, fixer):
        issue = Issue(
            type=IssueType.LARGE_RESPONSE,
            severity=Severity.MEDIUM,
            file_path="x.py",
            line_number=1,
            code_snippet="x = 1",
            estimated_monthly_cost=Decimal("10"),
            description="test",
            explanation="test",
        )
        assert fixer.generate_fix(issue, "x = 1\n") is None

    def test_generate_all_fixes(self, fixer, n_plus_one_issue):
        code = "for item in items:\n    result = db.query(item.id)\n    process(result)\n"
        fixes = asyncio.run(fixer.generate_all_fixes(
            [n_plus_one_issue],
            {"app.py": code}
        ))
        assert len(fixes) == 1


class TestFixApplier:
    def test_applies_fix(self, tmp_path):
        target = tmp_path / "test.py"
        target.write_text("a = await get_a()\nb = await get_b()\n")

        fix = Fix(
            issue=Issue(
                type=IssueType.SEQUENTIAL_ASYNC,
                severity=Severity.HIGH,
                file_path=str(target),
                line_number=1,
                code_snippet="a = await get_a()\nb = await get_b()",
                estimated_monthly_cost=Decimal("50"),
                description="test",
                explanation="test",
            ),
            original_code="a = await get_a()\nb = await get_b()",
            fixed_code="a, b = await asyncio.gather(\n    get_a(),\n    get_b()\n)",
            explanation="parallel",
            confidence=0.95,
            auto_apply_safe=True,
            savings_monthly=Decimal("45"),
        )

        applier = FixApplier(dry_run=False, validate=False)
        result = applier.apply_fix(fix)
        assert result.success
        assert "asyncio.gather" in target.read_text()

    def test_dry_run_does_not_modify(self, tmp_path):
        target = tmp_path / "test.py"
        original = "a = await get_a()\nb = await get_b()\n"
        target.write_text(original)

        fix = Fix(
            issue=Issue(
                type=IssueType.SEQUENTIAL_ASYNC,
                severity=Severity.HIGH,
                file_path=str(target),
                line_number=1,
                code_snippet="a = await get_a()\nb = await get_b()",
                estimated_monthly_cost=Decimal("50"),
                description="test",
                explanation="test",
            ),
            original_code="a = await get_a()\nb = await get_b()",
            fixed_code="a, b = await asyncio.gather(get_a(), get_b())",
            explanation="parallel",
            confidence=0.95,
            auto_apply_safe=True,
            savings_monthly=Decimal("45"),
        )

        applier = FixApplier(dry_run=True, validate=False)
        result = applier.apply_fix(fix)
        assert result.success
        assert target.read_text() == original

    def test_fails_if_code_not_found(self, tmp_path):
        target = tmp_path / "test.py"
        target.write_text("completely different code\n")

        fix = Fix(
            issue=Issue(
                type=IssueType.SEQUENTIAL_ASYNC,
                severity=Severity.HIGH,
                file_path=str(target),
                line_number=1,
                code_snippet="x",
                estimated_monthly_cost=Decimal("50"),
                description="test",
                explanation="test",
            ),
            original_code="not in file",
            fixed_code="replaced",
            explanation="test",
            confidence=0.9,
            auto_apply_safe=True,
            savings_monthly=Decimal("10"),
        )

        applier = FixApplier(dry_run=False, validate=False)
        result = applier.apply_fix(fix)
        assert not result.success
        assert "not found" in result.error
