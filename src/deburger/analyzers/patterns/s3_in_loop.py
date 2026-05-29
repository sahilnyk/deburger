import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector

_LOOP_RE = re.compile(r'for\s+.*\s+in\s+|for\s*\(|\.forEach\(|\.map\(|while\s')
_STORAGE_PATTERNS = [
    re.compile(p) for p in [
        r's3\.get_object\(',
        r's3\.put_object\(',
        r's3\.download_file\(',
        r's3\.upload_file\(',
        r'\.getObject\(',
        r'\.putObject\(',
        r'\.upload\(',
        r'storage\.bucket\(',
        r'\.download_blob\(',
        r'\.upload_from_string\(',
        r'blob\.download\(',
    ]
]


class S3InLoopDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "s3_in_loop"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".js", ".ts"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split('\n')

        in_loop = False
        loop_start = 0

        for i, line in enumerate(lines, 1):
            if _LOOP_RE.search(line):
                in_loop = True
                loop_start = i

            if in_loop and i > loop_start + 1:
                indent_start = len(lines[loop_start - 1]) - len(lines[loop_start - 1].lstrip())
                current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_start + 1

                if current_indent <= indent_start and line.strip():
                    in_loop = False

            if in_loop and any(p.search(line) for p in _STORAGE_PATTERNS):
                snippet = '\n'.join(lines[max(0, loop_start - 1):min(len(lines), i + 1)])

                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                iterations = 100
                total_s3_calls = monthly_requests * iterations
                cost = Decimal(total_s3_calls) * Decimal("0.0000004")

                issues.append(Issue(
                    type=IssueType.N_PLUS_ONE_QUERY,
                    severity=Severity.HIGH,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=snippet,
                    estimated_monthly_cost=cost,
                    description="S3/storage call inside loop",
                    explanation="making individual storage requests in a loop. batch operations are 10-100x cheaper",
                    fix_suggestion="use batch operations: s3.download_fileobj() with multipart, or collect keys and use batch get",
                    savings_monthly=cost * Decimal("0.90"),
                ))

                in_loop = False

        return issues
