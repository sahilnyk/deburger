"""Fix generation orchestrator."""

from typing import List, Optional

from deburger.models.error import ErrorInfo
from deburger.models.fix import Fix
from deburger.storage.cache import FixCache
from deburger.integrations.ai_provider import AIProvider


class FixGenerator:
    """Generate fixes using AI providers with caching."""

    def __init__(
        self,
        providers: List[AIProvider],
        cache: Optional[FixCache] = None,
        max_candidates: int = 3,
    ):
        """
        Initialize fix generator.

        Args:
            providers: List of AI providers (tried in order)
            cache: Fix cache (optional)
            max_candidates: Maximum fix candidates per error
        """
        self.providers = providers
        self.cache = cache or FixCache()
        self.max_candidates = max_candidates

    async def generate(self, error: ErrorInfo) -> List[Fix]:
        """
        Generate fix candidates for an error.

        Tries cache first, then falls back to AI providers.

        Args:
            error: Error to fix

        Returns:
            List of fix candidates

        Raises:
            Exception: If all providers fail
        """
        # Try cache first
        cached_fix = self.cache.get(error)
        if cached_fix:
            return [cached_fix]

        # Try providers in order
        last_error = None
        for provider in self.providers:
            try:
                fixes = await provider.generate_fixes(error, self.max_candidates)
                if fixes:
                    # Cache the best fix
                    best_fix = max(fixes, key=lambda f: f.confidence)
                    if best_fix.confidence > 0.8:
                        self.cache.put(error, best_fix)

                    return fixes

            except Exception as e:
                last_error = e
                continue

        # All providers failed
        if last_error:
            raise Exception(f"All AI providers failed: {last_error}")
        else:
            raise Exception("No fixes generated")

    async def generate_batch(self, errors: List[ErrorInfo]) -> dict[str, List[Fix]]:
        """
        Generate fixes for multiple errors.

        Args:
            errors: List of errors to fix

        Returns:
            Dictionary mapping error hash to fixes
        """
        results = {}

        for error in errors:
            try:
                fixes = await self.generate(error)
                results[error.error_hash] = fixes
            except Exception:
                results[error.error_hash] = []

        return results
