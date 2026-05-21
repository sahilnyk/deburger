import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector


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
            # detect filter/where without index hints
            if self._is_full_table_scan(line, lines, i):
                snippet = '\n'.join(lines[max(0, i-2):min(len(lines), i+2)])

                # full table scans on 100k+ row tables = disaster
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                # each scan reads all rows instead of indexed subset
                scan_cost = Decimal(monthly_requests) * Decimal("0.000004")  # RDS IOPS cost

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
        line_stripped = line.strip()

        # python ORM patterns without select_related
        if re.search(r'\.filter\(.*__contains|.*__icontains|.*__regex', line_stripped):
            return True

        # raw SQL without WHERE using index
        if re.search(r'SELECT\s+\*\s+FROM', line_stripped, re.IGNORECASE):
            # check if there's a WHERE with LIKE %...%
            context = '\n'.join(lines[max(0, line_num-1):min(len(lines), line_num+3)])
            if re.search(r"LIKE\s+'%.*%'", context, re.IGNORECASE):
                return True

        # mongo without index hint
        if re.search(r'\.find\(\{[^}]*\$regex', line_stripped):
            return True

        # django/sqlalchemy filter on text fields with contains
        if re.search(r'\.filter\(.*name.*=|.*title.*=|.*description.*=', line_stripped):
            # only flag if it's a text search pattern
            if 'icontains' in line_stripped or 'contains' in line_stripped:
                return True

        return False
