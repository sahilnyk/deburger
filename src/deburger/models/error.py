"""Error data models."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


@dataclass
class TracebackFrame:
    """Single frame in a traceback."""

    file_path: str
    line_number: int
    function_name: str
    code_line: str


@dataclass
class ErrorInfo:
    """Structured representation of a parsed error."""

    error_type: str
    message: str
    file_path: str
    line_number: int
    function_name: str
    traceback: List[TracebackFrame]
    code_context: str
    local_vars: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def error_hash(self) -> str:
        """Generate content-based hash for caching."""
        content = f"{self.error_type}:{self.message}:{self.file_path}:{self.code_context}"
        return hashlib.sha256(content.encode()).hexdigest()

    @property
    def short_hash(self) -> str:
        """Short version of hash for display."""
        return self.error_hash[:8]


@dataclass
class ErrorClassification:
    """Classification metadata for an error."""

    complexity: str  # "low", "medium", "high"
    category: str
    is_known_pattern: bool = False
    confidence: float = 0.0
    similar_errors: List[str] = field(default_factory=list)
