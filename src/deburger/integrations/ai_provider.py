"""AI provider interface."""

from typing import Protocol, List

from deburger.models.error import ErrorInfo
from deburger.models.fix import Fix


class AIProvider(Protocol):
    """Protocol for AI providers."""

    name: str

    async def generate_fixes(
        self,
        error: ErrorInfo,
        max_candidates: int = 3
    ) -> List[Fix]:
        """
        Generate fix candidates for an error.

        Args:
            error: The error to fix
            max_candidates: Maximum number of fix candidates

        Returns:
            List of Fix objects
        """
        ...
