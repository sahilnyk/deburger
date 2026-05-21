import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector


class ConnectionPoolDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "no_connection_pool"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".js", ".ts"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            if self._creates_connection_in_handler(line, lines, i, code):
                snippet = '\n'.join(lines[max(0, i-2):min(len(lines), i+2)])

                # new connection per request = ~50ms overhead each time
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                overhead_seconds = Decimal("0.05")  # 50ms per connection setup
                memory_gb = Decimal(config.get("traffic", {}).get("avg_memory_mb", 1024)) / Decimal(1024)

                cost = Decimal(monthly_requests) * overhead_seconds * memory_gb * Decimal("0.0000166667")

                issues.append(Issue(
                    type=IssueType.INEFFICIENT_QUERY,
                    severity=Severity.HIGH,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=snippet,
                    estimated_monthly_cost=cost,
                    description="creating new db connection per request",
                    explanation="opening a new database connection for each request adds ~50ms overhead and wastes resources",
                    fix_suggestion="use a connection pool (e.g., sqlalchemy pool, pg-pool, knex pool)",
                    savings_monthly=cost * Decimal("0.90"),
                ))

        return issues

    def _creates_connection_in_handler(self, line: str, lines: List[str], line_num: int, code: str) -> bool:
        stripped = line.strip()

        # python: creating connection inside function
        python_patterns = [
            r'psycopg2\.connect\(',
            r'pymysql\.connect\(',
            r'sqlite3\.connect\(',
            r'create_engine\(',
            r'MongoClient\(',
            r'redis\.Redis\(',
            r'boto3\.client\(',
        ]

        js_patterns = [
            r'new\s+Pool\(',
            r'createConnection\(',
            r'mongoose\.connect\(',
            r'new\s+MongoClient\(',
            r'createClient\(',
        ]

        all_patterns = python_patterns + js_patterns

        for pattern in all_patterns:
            if re.search(pattern, stripped):
                # check if it's inside a function (not module level)
                if self._is_inside_function(lines, line_num):
                    # check if there's no pooling nearby
                    context = '\n'.join(lines[max(0, line_num-10):min(len(lines), line_num+5)])
                    if 'pool' not in context.lower() and 'Pool' not in context:
                        return True

        return False

    def _is_inside_function(self, lines: List[str], line_num: int) -> bool:
        # walk backwards to find if we're inside a function
        for i in range(line_num - 2, max(0, line_num - 20), -1):
            stripped = lines[i].strip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                return True
            if stripped.startswith('function ') or '=>' in stripped:
                return True

        return False
