"""Calculate code quality metrics."""

import ast
from dataclasses import dataclass


@dataclass
class CodeMetrics:
    complexity: int
    maintainability: float
    lines_of_code: int
    comment_ratio: float
    test_coverage: float
    overall_score: float


class MetricsCalculator:
    def calculate(self, filepath: str, content: str) -> CodeMetrics:
        if not filepath.endswith(".py"):
            return self._empty_metrics()

        complexity = self._cyclomatic_complexity(content)
        loc = self._count_loc(content)
        comment_ratio = self._comment_ratio(content)

        maintainability = self._maintainability_index(complexity, loc, comment_ratio)
        overall = self._calculate_overall(complexity, maintainability, comment_ratio)

        return CodeMetrics(
            complexity=complexity,
            maintainability=maintainability,
            lines_of_code=loc,
            comment_ratio=comment_ratio,
            test_coverage=0.0,
            overall_score=overall,
        )

    def _cyclomatic_complexity(self, content: str) -> int:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0

        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _count_loc(self, content: str) -> int:
        lines = [line.strip() for line in content.split("\n")]
        return len([line for line in lines if line and not line.startswith("#")])

    def _comment_ratio(self, content: str) -> float:
        lines = content.split("\n")
        total = len(lines)
        comments = sum(1 for line in lines if line.strip().startswith("#"))
        return comments / total if total > 0 else 0.0

    def _maintainability_index(self, complexity: int, loc: int, comment_ratio: float) -> float:
        if loc == 0:
            return 100.0
        return max(0, 100 - (complexity * 2) - (loc / 10) + (comment_ratio * 10))

    def _calculate_overall(self, complexity: int, maintainability: float, comment_ratio: float) -> float:
        complexity_score = max(0, 100 - complexity * 5)
        return (complexity_score * 0.4 + maintainability * 0.4 + comment_ratio * 100 * 0.2)

    def _empty_metrics(self) -> CodeMetrics:
        return CodeMetrics(
            complexity=0,
            maintainability=0.0,
            lines_of_code=0,
            comment_ratio=0.0,
            test_coverage=0.0,
            overall_score=0.0,
        )
