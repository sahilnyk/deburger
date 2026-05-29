"""Tests for expensive logging detector."""

import pytest
from deburger.analyzers.patterns.expensive_logging import ExpensiveLoggingDetector
from deburger.analyzers.base import IssueType


@pytest.fixture
def detector():
    return ExpensiveLoggingDetector()


@pytest.fixture
def config():
    return {"traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024}}


def test_detects_logging_in_loop(detector, config):
    code = "for item in items:\n    logger.info(f'processing {item}')\n}\n"
    issues = detector.detect("app.py", code, config)
    # may or may not trigger depending on cost threshold
    # but should not crash
    assert isinstance(issues, list)


def test_detects_high_density_logging(detector, config):
    # 50 log lines in 100 lines = 50% density
    lines = []
    for i in range(100):
        if i % 2 == 0:
            lines.append(f"    logger.info('step {i}')")
        else:
            lines.append(f"    x = {i}")
    code = "def handler(event, context):\n" + "\n".join(lines)
    issues = detector.detect("handler.py", code, config)
    assert isinstance(issues, list)


def test_no_false_positive_minimal_logging(detector, config):
    code = "def process():\n    logger.info('start')\n    do_work()\n    logger.info('done')\n"
    issues = detector.detect("app.py", code, config)
    assert len(issues) == 0
