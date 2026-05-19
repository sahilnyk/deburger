"""Tests for metrics calculator."""

import pytest

from deburger.metrics.calculator import MetricsCalculator


def test_simple_function_low_complexity():
    calc = MetricsCalculator()
    code = """
def add(x, y):
    return x + y
"""
    metrics = calc.calculate("test.py", code)

    assert metrics.complexity <= 2
    assert metrics.maintainability > 80
    assert metrics.overall_score > 70


def test_complex_function_high_complexity():
    calc = MetricsCalculator()
    code = """
def complex_logic(x):
    if x > 10:
        if x < 20:
            for i in range(x):
                if i % 2 == 0:
                    return i
    elif x < 5:
        while x > 0:
            x -= 1
    return 0
"""
    metrics = calc.calculate("test.py", code)

    assert metrics.complexity > 5


def test_comment_ratio_calculation():
    calc = MetricsCalculator()
    code = """
def func():
    pass
"""
    metrics = calc.calculate("test.py", code)

    assert metrics.comment_ratio >= 0.0


def test_non_python_file():
    calc = MetricsCalculator()
    code = "console.log('hello');"
    metrics = calc.calculate("test.js", code)

    assert metrics.complexity == 0
    assert metrics.lines_of_code == 0
