import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector


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

        # count log statements
        log_lines = []
        in_loop = False
        loop_log_lines = []

        for i, line in enumerate(lines, 1):
            # track loops
            if re.search(r'for\s+|while\s+|\.forEach|\.map\(', line):
                in_loop = True
                loop_log_lines = []

            if in_loop and self._is_log_statement(line):
                loop_log_lines.append(i)

            if in_loop and '}' in line and not self._is_log_statement(line):
                if loop_log_lines:
                    # logging inside a loop - very expensive on cloudwatch
                    snippet = '\n'.join(lines[max(0, loop_log_lines[0]-2):min(len(lines), loop_log_lines[-1]+1)])

                    monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                    iterations = 100
                    log_events = monthly_requests * iterations * len(loop_log_lines)

                    # CloudWatch: $0.50 per GB ingested, assume 200 bytes per log
                    log_size_gb = Decimal(log_events) * Decimal("200") / Decimal(1024**3)
                    ingest_cost = log_size_gb * Decimal("0.50")

                    # storage: $0.03 per GB/month
                    storage_cost = log_size_gb * Decimal("0.03")

                    total_cost = ingest_cost + storage_cost

                    if total_cost > Decimal("10"):  # only flag if > $10/mo
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

            if self._is_log_statement(line):
                log_lines.append(i)

        # check overall log density
        if len(lines) > 0:
            log_ratio = len(log_lines) / len(lines)

            # more than 20% of lines are logs = probably over-logging
            if log_ratio > 0.20 and len(log_lines) > 10:
                monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
                log_events = monthly_requests * len(log_lines)

                log_size_gb = Decimal(log_events) * Decimal("200") / Decimal(1024**3)
                cost = log_size_gb * Decimal("0.50")

                if cost > Decimal("50"):  # only flag if significant
                    issues.append(Issue(
                        type=IssueType.LARGE_RESPONSE,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=1,
                        code_snippet=f"# {len(log_lines)} log statements in {len(lines)} lines ({log_ratio*100:.0f}%)",
                        estimated_monthly_cost=cost,
                        description=f"excessive logging ({len(log_lines)} statements)",
                        explanation=f"high log density will cost ~${cost:.0f}/mo on CloudWatch at current traffic",
                        fix_suggestion="reduce logging, use log levels properly, add sampling for high-volume paths",
                        savings_monthly=cost * Decimal("0.60"),
                    ))

        return issues

    def _is_log_statement(self, line: str) -> bool:
        stripped = line.strip()

        patterns = [
            r'logger?\.(info|debug|warning|error|critical|warn)\(',
            r'console\.(log|info|warn|error|debug)\(',
            r'print\(',
            r'logging\.(info|debug|warning|error)\(',
        ]

        return any(re.search(p, stripped) for p in patterns)
