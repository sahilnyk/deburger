"""Test result data models."""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from deburger.models.error import ErrorInfo


@dataclass
class TestResult:
    """Results from running tests."""

    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: List[ErrorInfo] = field(default_factory=list)
    duration: float = 0.0
    output: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and len(self.errors) == 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
