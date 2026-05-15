"""Tests for test runner."""

import pytest
from deburger.core.test_runner import TestRunner


@pytest.fixture
def runner():
    return TestRunner()


def test_parse_pytest_output_success(runner):
    """Test parsing successful pytest output."""
    output = """
============================= test session starts ==============================
collected 5 items

tests/test_math.py::test_add PASSED
tests/test_math.py::test_subtract PASSED
tests/test_math.py::test_multiply PASSED
tests/test_math.py::test_divide PASSED
tests/test_math.py::test_modulo PASSED

============================== 5 passed in 0.12s ===============================
"""

    result = runner._parse_pytest_output(output, 0.12, 0)

    assert result.total_tests == 5
    assert result.passed == 5
    assert result.failed == 0
    assert result.skipped == 0
    assert result.all_passed is True
    assert result.success_rate == 100.0


def test_parse_pytest_output_with_failures(runner):
    """Test parsing pytest output with failures."""
    output = """
============================= test session starts ==============================
collected 10 items

tests/test_api.py::test_get_user PASSED
tests/test_api.py::test_create_user FAILED
tests/test_api.py::test_update_user PASSED
tests/test_api.py::test_delete_user FAILED

============================== 2 failed, 8 passed in 1.23s =====================

Traceback (most recent call last):
  File "tests/test_api.py", line 10, in test_create_user
    result = create_user(None)
TypeError: expected str, got NoneType
"""

    result = runner._parse_pytest_output(output, 1.23, 1)

    assert result.total_tests == 10
    assert result.passed == 8
    assert result.failed == 2
    assert result.all_passed is False
    assert result.success_rate == 80.0
    assert len(result.errors) >= 1


def test_parse_pytest_output_with_skipped(runner):
    """Test parsing pytest output with skipped tests."""
    output = """
============================= test session starts ==============================
collected 8 items

tests/test_integration.py::test_api PASSED
tests/test_integration.py::test_db SKIPPED
tests/test_integration.py::test_cache PASSED

============================== 2 passed, 1 skipped in 0.45s ===================
"""

    result = runner._parse_pytest_output(output, 0.45, 0)

    assert result.total_tests == 3
    assert result.passed == 2
    assert result.failed == 0
    assert result.skipped == 1


def test_parse_unittest_output_success(runner):
    """Test parsing successful unittest output."""
    output = """
.....
----------------------------------------------------------------------
Ran 5 tests in 0.123s

OK
"""

    result = runner._parse_unittest_output(output, 0.123, 0)

    assert result.total_tests == 5
    assert result.passed == 5
    assert result.failed == 0


def test_parse_unittest_output_with_failures(runner):
    """Test parsing unittest output with failures."""
    output = """
.F.F..
======================================================================
FAIL: test_divide (tests.test_math.TestMath)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_math.py", line 15, in test_divide
    self.assertEqual(divide(10, 2), 6)
AssertionError: 5 != 6

======================================================================
Ran 6 tests in 0.456s

FAILED (failures=2)
"""

    result = runner._parse_unittest_output(output, 0.456, 1)

    assert result.total_tests == 6
    assert result.passed == 4
    assert result.failed == 2


def test_build_pytest_command(runner):
    """Test building pytest command."""
    cmd = runner._build_command("tests/test_math.py", ["--maxfail=1"])

    assert "pytest" in cmd
    assert "-v" in cmd
    assert "--tb=short" in cmd
    assert "tests/test_math.py" in cmd
    assert "--maxfail=1" in cmd


def test_build_unittest_command():
    """Test building unittest command."""
    runner = TestRunner(test_runner="unittest")
    cmd = runner._build_command("tests.test_math", None)

    assert "python" in cmd
    assert "-m" in cmd
    assert "unittest" in cmd
    assert "tests.test_math" in cmd


def test_combine_results(runner):
    """Test combining multiple test results."""
    from deburger.models.test_result import TestResult

    result1 = TestResult(
        total_tests=5,
        passed=4,
        failed=1,
        skipped=0,
        duration=0.5,
    )

    result2 = TestResult(
        total_tests=3,
        passed=3,
        failed=0,
        skipped=0,
        duration=0.3,
    )

    combined = runner._combine_results([result1, result2])

    assert combined.total_tests == 8
    assert combined.passed == 7
    assert combined.failed == 1
    assert combined.duration == 0.8
