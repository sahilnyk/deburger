import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector

_CONTAINS_FILTER_RE = re.compile(r'\.filter\(.*__contains|.*__icontains|.*__regex')
_SELECT_STAR_RE = re.compile(r'SELECT\s+\*\s+FROM', re.IGNORECASE)
_LIKE_WILDCARD_RE = re.compile(r"LIKE\s+'%.*%'", re.IGNORECASE)
_MONGO_REGEX_RE = re.compile(r'\.find\(\{[^}]*\$regex')
_TEXT_FILTER_RE = re.compile(r'\.filter\(.*(?:name|title|description).*=')


class UnindexedQueryDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "unindexed_query"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".js", ".ts"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            if self._is_full_table_scan(line, lines, i):
                snippet = '\n'.join(lines[max(0, i - 2):min(len(lines), i + 2)])

                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                scan_cost = Decimal(monthly_requests) * Decimal("0.000004")

                issues.append(Issue(
                    type=IssueType.INEFFICIENT_QUERY,
                    severity=Severity.HIGH,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=snippet,
                    estimated_monthly_cost=scan_cost,
                    description="possible full table scan",
                    explanation="query filters on a column that likely has no index, causing full table scan on every request",
                    fix_suggestion="add database index on the filtered column, or use .select_related()/.prefetch_related()",
                    savings_monthly=scan_cost * Decimal("0.90"),
                ))

        return issues

    def _is_full_table_scan(self, line: str, lines: List[str], line_num: int) -> bool:
        stripped = line.strip()

        if _CONTAINS_FILTER_RE.search(stripped):
            return True

        if _SELECT_STAR_RE.search(stripped):
            context = '\n'.join(lines[max(0, line_num - 1):min(len(lines), line_num + 3)])
            if _LIKE_WILDCARD_RE.search(context):
                return True

        if _MONGO_REGEX_RE.search(stripped):
            return True

        if _TEXT_FILTER_RE.search(stripped):
            if 'icontains' in stripped or 'contains' in stripped:
                return True

        return False
