"""JavaScript/TypeScript code analyzer."""

from typing import List
from decimal import Decimal
from deburger.analyzers.base import BaseAnalyzer, Issue, IssueType, Severity
import re


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyze JavaScript/TypeScript code."""

    @property
    def name(self) -> str:
        return "javascript"

    @property
    def supported_languages(self) -> List[str]:
        return [".js", ".ts", ".jsx", ".tsx"]

    def analyze(self, file_path: str, code: str, config: dict) -> List[Issue]:
        """Analyze JavaScript code for expensive patterns."""
        issues = []

        if config.get("detect", {}).get("n_plus_one_queries", True):
            issues.extend(self._detect_n_plus_one_simple(file_path, code))

        if config.get("detect", {}).get("sequential_async", True):
            issues.extend(self._detect_sequential_async_simple(file_path, code))

        # run all pattern detectors
        from deburger.analyzers.patterns import ALL_PATTERNS
        for detector in ALL_PATTERNS:
            if detector.can_detect(file_path):
                issues.extend(detector.detect(file_path, code, config))

        return issues

    def parse_ast(self, code: str):
        """Parse JavaScript into AST - TODO: integrate proper parser."""
        # TODO: Use esprima or @babel/parser for real AST
        # For now, return None as placeholder
        return None

    def _detect_n_plus_one_simple(self, file_path: str, code: str) -> List[Issue]:
        """Simple pattern matching for N+1 queries in JS."""
        issues = []
        lines = code.split("\n")

        # Look for patterns like:
        # for (const item of items) {
        #     await db.query(...)
        # }

        in_loop = False
        loop_start_line = 0

        for i, line in enumerate(lines, 1):
            # Detect loop start
            if re.search(r'for\s*\(.*\)|\.forEach\(|\.map\(', line):
                in_loop = True
                loop_start_line = i

            # Detect loop end
            if in_loop and '}' in line:
                in_loop = False

            # Detect DB calls in loop
            if in_loop and re.search(r'(await|\.then)\s+.*\.(query|find|findOne|get)', line):
                code_snippet = "\n".join(lines[loop_start_line - 1:i + 1])

                # Estimate cost
                iterations = 500
                requests_per_day = 50000
                queries_per_month = iterations * requests_per_day * 30
                estimated_cost = Decimal(queries_per_month) * Decimal("0.0000002")

                issues.append(Issue(
                    type=IssueType.N_PLUS_ONE_QUERY,
                    severity=Severity.CRITICAL,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=code_snippet,
                    estimated_monthly_cost=estimated_cost,
                    description="N+1 query detected in loop",
                    explanation=(
                        f"Loop contains database query. "
                        f"Estimated {queries_per_month:,} queries/month."
                    ),
                    fix_suggestion=(
                        "Use bulk query:\n"
                        "const ids = items.map(item => item.id);\n"
                        "const results = await db.find({ id: { $in: ids } });"
                    ),
                    savings_monthly=estimated_cost * Decimal("0.95")
                ))

        return issues

    def _detect_sequential_async_simple(self, file_path: str, code: str) -> List[Issue]:
        """Simple pattern matching for sequential async in JS."""
        issues = []
        lines = code.split("\n")

        # Look for consecutive await statements
        await_lines = []

        for i, line in enumerate(lines, 1):
            if re.match(r'\s*(const|let|var).*=\s*await\s+', line):
                await_lines.append(i)
            elif await_lines:
                # Check if we have 2+ consecutive awaits
                if len(await_lines) >= 2 and await_lines[-1] == i - 1:
                    # Found sequential awaits
                    first = await_lines[0]
                    last = await_lines[-1]
                    code_snippet = "\n".join(lines[first - 1:last])

                    saved_seconds = len(await_lines) - 1
                    monthly_requests = 50000 * 30
                    savings = (
                        Decimal(monthly_requests) *
                        Decimal(saved_seconds) *
                        Decimal("0.0000166667")
                    )

                    issues.append(Issue(
                        type=IssueType.SEQUENTIAL_ASYNC,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=first,
                        code_snippet=code_snippet,
                        estimated_monthly_cost=savings,
                        description=f"Sequential await calls ({len(await_lines)} calls)",
                        explanation=(
                            f"Found {len(await_lines)} sequential awaits. "
                            f"Running parallel would save ~{saved_seconds}s per request."
                        ),
                        fix_suggestion=(
                            "Use Promise.all():\n"
                            "const [result1, result2] = await Promise.all([\n"
                            "    call1(),\n"
                            "    call2()\n"
                            "]);"
                        ),
                        savings_monthly=savings
                    ))

                await_lines = []

        return issues
