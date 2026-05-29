import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector

_CONNECTION_PATTERNS = [
    re.compile(p) for p in [
        r'psycopg2\.connect\(',
        r'pymysql\.connect\(',
        r'sqlite3\.connect\(',
        r'create_engine\(',
        r'MongoClient\(',
        r'redis\.Redis\(',
        r'boto3\.client\(',
        r'new\s+Pool\(',
        r'createConnection\(',
        r'mongoose\.connect\(',
        r'new\s+MongoClient\(',
        r'createClient\(',
    ]
]

_FUNC_RE = re.compile(r'^\s*(def |async def |function |.*=>)')


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
            if self._creates_connection_in_handler(line, lines, i):
                snippet = '\n'.join(lines[max(0, i - 2):min(len(lines), i + 2)])

                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                overhead_seconds = Decimal("0.05")
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

    def _creates_connection_in_handler(self, line: str, lines: List[str], line_num: int) -> bool:
        stripped = line.strip()

        for pattern in _CONNECTION_PATTERNS:
            if pattern.search(stripped):
                if self._is_inside_function(lines, line_num):
                    context = '\n'.join(lines[max(0, line_num - 10):min(len(lines), line_num + 5)])
                    if 'pool' not in context.lower():
                        return True

        return False

    def _is_inside_function(self, lines: List[str], line_num: int) -> bool:
        for i in range(line_num - 2, max(0, line_num - 20), -1):
            if _FUNC_RE.match(lines[i]):
                return True
        return False
