import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import BaseAnalyzer, Issue, IssueType, Severity

_LOOP_RE = re.compile(r'for\s*\(.*\)|\.forEach\(|\.map\(')
_DB_CALL_RE = re.compile(r'(await|\.then)\s+.*\.(query|find|findOne|get)')
_AWAIT_ASSIGN_RE = re.compile(r'\s*(const|let|var).*=\s*await\s+')
_AWAIT_EXTRACT_RE = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*await\s+(.+?);?$')


class JavaScriptAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "javascript"

    @property
    def supported_languages(self) -> List[str]:
        return [".js", ".ts", ".jsx", ".tsx"]

    def analyze(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []

        if config.get("detect", {}).get("n_plus_one_queries", True):
            issues.extend(self._detect_n_plus_one(file_path, code, config))

        if config.get("detect", {}).get("sequential_async", True):
            issues.extend(self._detect_sequential_async(file_path, code, config))

        from deburger.analyzers.patterns import ALL_PATTERNS
        for detector in ALL_PATTERNS:
            if detector.can_detect(file_path):
                issues.extend(detector.detect(file_path, code, config))

        lines = code.split("\n")
        issues = [
            i for i in issues
            if not self._is_suppressed(lines, i.line_number)
        ]

        return issues

    def _is_suppressed(self, lines: list, line_number: int) -> bool:
        idx = line_number - 1
        if idx < len(lines) and "deburger:ignore" in lines[idx]:
            return True
        if idx > 0 and "deburger:ignore" in lines[idx - 1]:
            return True
        return False

    def parse_ast(self, code: str):
        return None

    def _detect_n_plus_one(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split("\n")

        in_loop = False
        loop_start_line = 0

        for i, line in enumerate(lines, 1):
            if _LOOP_RE.search(line):
                in_loop = True
                loop_start_line = i

            if in_loop and '}' in line:
                in_loop = False

            if in_loop and _DB_CALL_RE.search(line):
                code_snippet = "\n".join(lines[loop_start_line - 1:i + 1])

                iterations = 500
                requests_per_day = config.get("traffic", {}).get("requests_per_day", 100000)
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
                    explanation=f"Loop contains database query. Estimated {queries_per_month:,} queries/month.",
                    fix_suggestion=(
                        "Use bulk query:\n"
                        "const ids = items.map(item => item.id);\n"
                        "const results = await db.find({ id: { $in: ids } });"
                    ),
                    savings_monthly=estimated_cost * Decimal("0.95")
                ))

        return issues

    def _detect_sequential_async(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split("\n")

        await_lines = []

        for i, line in enumerate(lines, 1):
            if _AWAIT_ASSIGN_RE.match(line):
                await_lines.append(i)
            else:
                if len(await_lines) >= 2:
                    issues.append(self._create_seq_issue(await_lines, lines, config, file_path))
                await_lines = []

        if len(await_lines) >= 2:
            issues.append(self._create_seq_issue(await_lines, lines, config, file_path))

        return issues

    def _create_seq_issue(self, await_lines: list, lines: list, config: dict, file_path: str) -> Issue:
        first = await_lines[0]
        last = await_lines[-1]
        code_snippet = "\n".join(lines[first - 1:last])

        saved_seconds = len(await_lines) - 1
        monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
        savings = Decimal(monthly_requests) * Decimal(saved_seconds) * Decimal("0.0000166667")

        return Issue(
            type=IssueType.SEQUENTIAL_ASYNC,
            severity=Severity.HIGH,
            file_path=file_path,
            line_number=first,
            code_snippet=code_snippet,
            estimated_monthly_cost=savings,
            description=f"Sequential await calls ({len(await_lines)} calls)",
            explanation=f"Found {len(await_lines)} sequential awaits. Running parallel would save ~{saved_seconds}s per request.",
            fix_suggestion="Use Promise.all():\nconst [result1, result2] = await Promise.all([\n    call1(),\n    call2()\n]);",
            savings_monthly=savings
        )
