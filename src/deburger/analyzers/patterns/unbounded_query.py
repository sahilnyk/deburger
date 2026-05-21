import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector


class UnboundedQueryDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "unbounded_query"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".js", ".ts"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            if self._is_unbounded_query(line, lines, i):
                snippet = '\n'.join(lines[max(0, i-2):min(len(lines), i+2)])

                # unbounded = returns ALL rows, memory explosion + slow
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                # assume 10x more data transferred than needed
                extra_transfer_gb = Decimal(monthly_requests) * Decimal("0.001") / Decimal(1024)  # 1KB extra per request
                transfer_cost = extra_transfer_gb * Decimal("0.09")  # $0.09/GB transfer

                # extra compute from processing all rows
                memory_gb = Decimal(config.get("traffic", {}).get("avg_memory_mb", 1024)) / Decimal(1024)
                extra_seconds = Decimal("0.5")  # 500ms extra per request
                compute_cost = Decimal(monthly_requests) * extra_seconds * memory_gb * Decimal("0.0000166667")

                total_cost = transfer_cost + compute_cost

                issues.append(Issue(
                    type=IssueType.LARGE_RESPONSE,
                    severity=Severity.CRITICAL,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=snippet,
                    estimated_monthly_cost=total_cost,
                    description="unbounded query - no LIMIT",
                    explanation="query returns all rows without pagination. as data grows this will OOM or timeout",
                    fix_suggestion="add .limit() or LIMIT clause, implement cursor-based pagination",
                    savings_monthly=total_cost * Decimal("0.85"),
                ))

        return issues

    def _is_unbounded_query(self, line: str, lines: List[str], line_num: int) -> bool:
        stripped = line.strip()

        # check nearby lines for limit/pagination
        context = '\n'.join(lines[max(0, line_num-3):min(len(lines), line_num+5)]).lower()

        # if there's already a limit nearby, skip
        if 'limit' in context or 'paginate' in context or 'pagination' in context:
            return False
        if '[:' in context or 'slice' in context or 'take(' in context:
            return False

        # python: .all() without limit
        if re.search(r'\.all\(\)', stripped):
            return True

        # python: .objects.filter() without [:n]
        if re.search(r'\.objects\.(filter|exclude)\(', stripped):
            if 'limit' not in context and '[:' not in context:
                return True

        # SQL: SELECT without LIMIT
        if re.search(r'SELECT.*FROM', stripped, re.IGNORECASE):
            if 'limit' not in context:
                return True

        # mongo: .find() without .limit()
        if re.search(r'\.find\(', stripped):
            if '.limit(' not in context and '.findOne(' not in stripped:
                return True

        # js: find without limit
        if re.search(r'\.findMany\(', stripped):
            if 'take' not in context and 'limit' not in context:
                return True

        return False
