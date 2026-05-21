import ast
import re
from typing import List
from decimal import Decimal
from deburger.analyzers.base import Issue, IssueType, Severity
from deburger.analyzers.patterns.base import PatternDetector

# heavy imports that kill lambda cold starts
HEAVY_IMPORTS = {
    "pandas": 250,       # ~250ms cold start
    "numpy": 150,        # ~150ms
    "scipy": 300,        # ~300ms
    "tensorflow": 2000,  # ~2s lol
    "torch": 1500,       # ~1.5s
    "sklearn": 400,      # ~400ms
    "boto3": 100,        # ~100ms (if not pre-bundled)
    "sqlalchemy": 200,   # ~200ms
    "django": 500,       # ~500ms
    "flask": 80,         # ~80ms
    "fastapi": 120,      # ~120ms
    "matplotlib": 400,   # ~400ms
    "pillow": 200,       # ~200ms
    "PIL": 200,
    "cv2": 500,          # ~500ms
    "transformers": 1500,
}


class ColdStartDetector(PatternDetector):
    @property
    def name(self) -> str:
        return "cold_start"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py"]

    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        issues = []

        # only matters for lambda/cloud function code
        if not self._looks_like_lambda(code, file_path):
            return issues

        lines = code.split('\n')

        # find top-level heavy imports
        heavy_found = []
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(?:import|from)\s+(\w+)', line)
            if match:
                module = match.group(1)
                if module in HEAVY_IMPORTS:
                    heavy_found.append((i, module, HEAVY_IMPORTS[module]))

        if not heavy_found:
            return issues

        total_cold_start_ms = sum(ms for _, _, ms in heavy_found)

        # only flag if cold start > 500ms
        if total_cold_start_ms < 500:
            return issues

        modules = ', '.join(m for _, m, _ in heavy_found)
        first_line = heavy_found[0][0]
        snippet = '\n'.join(lines[first_line-1:first_line+len(heavy_found)])

        # cost: cold starts * extra duration * lambda pricing
        # assume 5% of invocations are cold starts
        monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
        cold_starts = int(monthly_requests * 0.05)
        wasted_seconds = Decimal(total_cold_start_ms) / Decimal(1000)
        memory_gb = Decimal(config.get("traffic", {}).get("avg_memory_mb", 1024)) / Decimal(1024)

        cost = Decimal(cold_starts) * wasted_seconds * memory_gb * Decimal("0.0000166667")

        issues.append(Issue(
            type=IssueType.OVER_PROVISIONED_LAMBDA,
            severity=Severity.HIGH if total_cold_start_ms > 1000 else Severity.MEDIUM,
            file_path=file_path,
            line_number=first_line,
            code_snippet=snippet,
            estimated_monthly_cost=cost,
            description=f"heavy imports causing {total_cold_start_ms}ms cold start",
            explanation=f"importing {modules} at top level adds ~{total_cold_start_ms}ms to every cold start",
            fix_suggestion="move heavy imports inside the handler function (lazy import)",
            savings_monthly=cost * Decimal("0.80"),
        ))

        return issues

    def _looks_like_lambda(self, code: str, file_path: str) -> bool:
        # check if file looks like a lambda handler
        if 'handler' in file_path or 'lambda' in file_path:
            return True

        if 'def handler(' in code or 'def lambda_handler(' in code:
            return True

        if 'def main(event' in code:
            return True

        # serverless framework / SAM patterns
        if 'def handler(event, context)' in code:
            return True

        return False
