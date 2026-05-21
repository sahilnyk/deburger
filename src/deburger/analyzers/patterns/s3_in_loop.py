import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector


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
            # detect loop
            if re.search(r'for\s+.*\s+in\s+|for\s*\(|\.forEach\(|\.map\(|while\s', line):
                in_loop = True
                loop_start = i

            # detect loop end (simplified)
            if in_loop and i > loop_start + 1:
                indent_start = len(lines[loop_start-1]) - len(lines[loop_start-1].lstrip())
                current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_start + 1

                if current_indent <= indent_start and line.strip():
                    in_loop = False

            # detect S3/storage calls in loop
            if in_loop and self._is_storage_call(line):
                snippet = '\n'.join(lines[max(0, loop_start-1):min(len(lines), i+1)])

                # S3 pricing: $0.0004 per 1000 GET, $0.005 per 1000 PUT
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                iterations = 100  # conservative
                total_s3_calls = monthly_requests * iterations

                # mix of GET/PUT
                cost = Decimal(total_s3_calls) * Decimal("0.0000004")

                issues.append(Issue(
                    type=IssueType.N_PLUS_ONE_QUERY,
                    severity=Severity.HIGH,
                    file_path=file_path,
                    line_number=i,
                    code_snippet=snippet,
                    estimated_monthly_cost=cost,
                    description="S3/storage call inside loop",
                    explanation=f"making individual storage requests in a loop. batch operations are 10-100x cheaper",
                    fix_suggestion="use batch operations: s3.download_fileobj() with multipart, or collect keys and use batch get",
                    savings_monthly=cost * Decimal("0.90"),
                ))

                in_loop = False  # only report once per loop

        return issues

    def _is_storage_call(self, line: str) -> bool:
        patterns = [
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

        return any(re.search(p, line) for p in patterns)
