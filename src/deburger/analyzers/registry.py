"""Analyzer registry."""

from typing import Dict, List, Optional
from deburger.analyzers.base import BaseAnalyzer


class AnalyzerRegistry:
    """Registry for code analyzers."""

    _analyzers: Dict[str, BaseAnalyzer] = {}

    @classmethod
    def register(cls, analyzer: BaseAnalyzer):
        """Register an analyzer."""
        cls._analyzers[analyzer.name] = analyzer

    @classmethod
    def get(cls, name: str) -> Optional[BaseAnalyzer]:
        """Get analyzer by name."""
        return cls._analyzers.get(name)

    @classmethod
    def get_for_file(cls, file_path: str) -> Optional[BaseAnalyzer]:
        """Get appropriate analyzer for file."""
        for analyzer in cls._analyzers.values():
            if analyzer.can_analyze(file_path):
                return analyzer
        return None

    @classmethod
    def list_analyzers(cls) -> List[str]:
        """List all registered analyzers."""
        return list(cls._analyzers.keys())
