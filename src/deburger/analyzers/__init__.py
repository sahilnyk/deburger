"""AST-based code analyzers."""

from deburger.analyzers.base import BaseAnalyzer, Issue, IssueType
from deburger.analyzers.python_analyzer import PythonAnalyzer
from deburger.analyzers.javascript_analyzer import TypeScriptAnalyzer
from deburger.analyzers.registry import AnalyzerRegistry

# Auto-register analyzers
AnalyzerRegistry.register(PythonAnalyzer())
AnalyzerRegistry.register(TypeScriptAnalyzer())

__all__ = [
    "BaseAnalyzer",
    "Issue",
    "IssueType",
    "PythonAnalyzer",
    "TypeScriptAnalyzer",
    "AnalyzerRegistry",
]
