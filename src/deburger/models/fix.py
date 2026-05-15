"""Fix data models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CodeChange:
    """Represents a single code change."""

    file_path: str
    line_start: int
    line_end: int
    old_code: str
    new_code: str


@dataclass
class Fix:
    """AI-generated fix for an error."""

    id: int
    explanation: str
    changes: List[CodeChange]
    confidence: float
    reasoning: str

    @property
    def confidence_percent(self) -> int:
        """Confidence as percentage."""
        return int(self.confidence * 100)
