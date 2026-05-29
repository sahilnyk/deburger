import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector

_LOOP_RE = re.compile(r'for\s+|while\s+|\.forEach|\.map\(')
_LOG_RE = re.compile(
    r'logger?\.(info|debug|warning|error|critical|warn)\('
    r'|console\.(log|info|warn|error|debug)\('
    r'|print\('
    r'|logging\.(info|debug|warning|error)\('
)


class ExpensiveLoggingDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "expensive_logging"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".js", ".ts"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []
        lines = code.split('\n')

        log_lines = []
        in_loop = False
        loop_log_lines = []

        for i, line in enumerate(lines, 1):
            if _LOOP_RE.search(line):
                in_loop = True
                loop_log_lines = []

            is_log = bool(_LOG_RE.search(line.strip()))

            if in_loop and is_log:
                loop_log_lines.append(i)

            if in_loop and '}' in line and not is_log:
                if loop_log_lines:
                    snippet = '\n'.join(lines[max(0, loop_log_lines[0] - 2):min(len(lines), loop_log_lines[-1] + 1)])

                    monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                    iterations = 100
                    log_events = monthly_requests * iterations * len(loop_log_lines)

                    log_size_gb = Decimal(log_events) * Decimal("200") / Decimal(1024 ** 3)
                    ingest_cost = log_size_gb * Decimal("0.50")
                    storage_cost = log_size_gb * Decimal("0.03")
                    total_cost = ingest_cost + storage_cost

                    if total_cost > Decimal("10"):
                        issues.append(Issue(
                            type=IssueType.LARGE_RESPONSE,
                            severity=Severity.MEDIUM,
                            file_path=file_path,
                            line_number=loop_log_lines[0],
                            code_snippet=snippet,
                            estimated_monthly_cost=total_cost,
                            description="expensive logging in loop",
                            explanation=f"logging inside loop generates ~{log_events:,} log events/month on CloudWatch",
                            fix_suggestion="move logging outside loop, use sampling, or reduce log level to DEBUG",
                            savings_monthly=total_cost * Decimal("0.80"),
                        ))

                in_loop = False
                loop_log_lines = []

            if is_log:
                log_lines.append(i)

        if len(lines) > 0:
            log_ratio = len(log_lines) / len(lines)

            if log_ratio > 0.20 and len(log_lines) > 10:
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                log_events = monthly_requests * len(log_lines)

                log_size_gb = Decimal(log_events) * Decimal("200") / Decimal(1024 ** 3)
                cost = log_size_gb * Decimal("0.50")

                if cost > Decimal("50"):
                    issues.append(Issue(
                        type=IssueType.LARGE_RESPONSE,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=1,
                        code_snippet=f"# {len(log_lines)} log statements in {len(lines)} lines ({log_ratio * 100:.0f}%)",
                        estimated_monthly_cost=cost,
                        description=f"excessive logging ({len(log_lines)} statements)",
                        explanation=f"high log density will cost ~${cost:.0f}/mo on CloudWatch at current traffic",
                        fix_suggestion="reduce logging, use log levels properly, add sampling for high-volume paths",
                        savings_monthly=cost * Decimal("0.60"),
                    ))

        return issues
