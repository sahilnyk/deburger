"""Base classes for code analyzers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any
from decimal import Decimal


class IssueType(Enum):
    """Types of code issues that cost money."""
    N_PLUS_ONE_QUERY = "n_plus_one_query"
    SEQUENTIAL_ASYNC = "sequential_async"
    OVER_PROVISIONED_LAMBDA = "over_provisioned_lambda"
    OVER_PROVISIONED_CONTAINER = "over_provisioned_container"
    MISSING_CACHING = "missing_caching"
    LARGE_RESPONSE = "large_response"
    INEFFICIENT_QUERY = "inefficient_query"


class Severity(Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Issue:
    """Detected code issue."""
    type: IssueType
    severity: Severity
    file_path: str
    line_number: int
    code_snippet: str

    # Cost impact
    estimated_monthly_cost: Decimal

    # Details
    description: str
    explanation: str

    # Fix suggestion
    fix_suggestion: Optional[str] = None
    fixed_code: Optional[str] = None
    savings_monthly: Optional[Decimal] = None

    # Context
    context: dict = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class BaseAnalyzer(ABC):
    """Base class for language-specific analyzers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Analyzer name."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """List of supported file extensions."""
        pass

    @abstractmethod
    def analyze(self, file_path: str, code: str, config: dict) -> List[Issue]:
        """
        Analyze code and return detected issues.

        Args:
            file_path: Path to the file being analyzed
            code: Source code content
            config: Configuration dict

        Returns:
            List of detected issues
        """
        pass

    @abstractmethod
    def parse_ast(self, code: str) -> Any:
        """
        Parse code into AST.

        Returns:
            AST object (language-specific)
        """
        pass

    def can_analyze(self, file_path: str) -> bool:
        """Check if this analyzer can handle the file."""
        return any(file_path.endswith(ext) for ext in self.supported_languages)
