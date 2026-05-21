"""Python code analyzer using AST."""

import ast
from typing import List
from decimal import Decimal
from deburger.analyzers.base import BaseAnalyzer, Issue, IssueType, Severity


class PythonAnalyzer(BaseAnalyzer):
    """Analyze Python code using AST."""

    @property
    def name(self) -> str:
        return "python"

    @property
    def supported_languages(self) -> List[str]:
        return [".py"]

    def analyze(self, file_path: str, code: str, config: dict) -> List[Issue]:
        """Analyze Python code for expensive patterns."""
        issues = []

        try:
            tree = self.parse_ast(code)
        except SyntaxError:
            return issues

        if config.get("detect", {}).get("n_plus_one_queries", True):
            issues.extend(self._detect_n_plus_one(tree, file_path, code, config))

        if config.get("detect", {}).get("sequential_async", True):
            issues.extend(self._detect_sequential_async(tree, file_path, code, config))

        # run all pattern detectors
        from deburger.analyzers.patterns import ALL_PATTERNS
        for detector in ALL_PATTERNS:
            if detector.can_detect(file_path):
                issues.extend(detector.detect(file_path, code, config))

        return issues

    def parse_ast(self, code: str) -> ast.AST:
        """Parse Python code into AST."""
        return ast.parse(code)

    def _detect_n_plus_one(
        self,
        tree: ast.AST,
        file_path: str,
        code: str,
        config: dict = None
    ) -> List[Issue]:
        issues = []
        lines = code.split("\n")
        config = config or {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.For):
                continue

            # Check if loop body contains database calls
            db_calls = self._find_db_calls_in_loop(node)

            if db_calls:
                # Found potential N+1 pattern
                line_num = node.lineno
                code_snippet = "\n".join(lines[line_num - 1:line_num + 3])

                iterations = 500
                requests_per_day = config.get("traffic", {}).get("requests_per_day", 100000)
                queries_per_month = iterations * requests_per_day * 30

                # Cost: ~$0.0000002 per query on RDS
                estimated_cost = Decimal(queries_per_month) * Decimal("0.0000002")

                issues.append(Issue(
                    type=IssueType.N_PLUS_ONE_QUERY,
                    severity=Severity.CRITICAL,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=code_snippet,
                    estimated_monthly_cost=estimated_cost,
                    description=f"N+1 query detected in loop",
                    explanation=(
                        f"Loop contains database query that will execute "
                        f"once per iteration. With {iterations} iterations "
                        f"and {requests_per_day} requests/day, this creates "
                        f"{queries_per_month:,} queries/month."
                    ),
                    fix_suggestion=(
                        "Move query outside loop and use bulk query:\n"
                        "ids = [item.id for item in items]\n"
                        "results = db.query().filter(id.in_(ids)).all()"
                    ),
                    savings_monthly=estimated_cost * Decimal("0.95"),  # 95% savings
                    context={
                        "db_calls": len(db_calls),
                        "estimated_iterations": iterations
                    }
                ))

        return issues

    def _find_db_calls_in_loop(self, for_node: ast.For) -> List[ast.Call]:
        """Find database calls inside a for loop."""
        db_calls = []

        # Common ORM patterns
        db_patterns = [
            "db.query",
            "db.get",
            "db.execute",
            ".query(",
            ".filter(",
            ".get(",
            "Session.query",
            "query.filter",
        ]

        for node in ast.walk(for_node):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else str(node.func)

                # Check if it's a database call
                if any(pattern in call_str for pattern in db_patterns):
                    db_calls.append(node)

        return db_calls

    def _detect_sequential_async(
        self,
        tree: ast.AST,
        file_path: str,
        code: str,
        config: dict = None
    ) -> List[Issue]:
        issues = []
        lines = code.split("\n")
        config = config or {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue

            awaits = []
            for stmt in node.body:
                if isinstance(stmt, (ast.Assign, ast.Expr)):
                    if self._contains_await(stmt):
                        awaits.append(stmt)
                    elif awaits:
                        # Reset if we hit non-await statement
                        if len(awaits) >= 2:
                            # Found sequential awaits!
                            issues.append(self._create_sequential_async_issue(
                                awaits,
                                file_path,
                                lines,
                                config
                            ))
                        awaits = []

            # Check at end of function
            if len(awaits) >= 2:
                issues.append(self._create_sequential_async_issue(
                    awaits,
                    file_path,
                    lines
                ))

        return issues

    def _contains_await(self, node: ast.AST) -> bool:
        """Check if node contains await expression."""
        for child in ast.walk(node):
            if isinstance(child, ast.Await):
                return True
        return False

    def _create_sequential_async_issue(
        self,
        await_nodes: List[ast.AST],
        file_path: str,
        lines: List[str],
        config: dict = None
    ) -> Issue:
        config = config or {}

        first_line = await_nodes[0].lineno
        last_line = await_nodes[-1].lineno
        code_snippet = "\n".join(lines[first_line - 1:last_line + 1])

        saved_seconds = len(await_nodes) - 1
        monthly_requests = config.get("traffic", {}).get("requests_per_day", 100000) * 30
        cost_per_gb_second = Decimal("0.0000166667")

        savings = (
            Decimal(monthly_requests) *
            Decimal(saved_seconds) *
            cost_per_gb_second
        )

        return Issue(
            type=IssueType.SEQUENTIAL_ASYNC,
            severity=Severity.HIGH,
            file_path=file_path,
            line_number=first_line,
            code_snippet=code_snippet,
            estimated_monthly_cost=savings,
            description=f"Sequential async calls ({len(await_nodes)} calls)",
            explanation=(
                f"Found {len(await_nodes)} sequential await calls. "
                f"Running them in parallel would save ~{saved_seconds}s per request."
            ),
            fix_suggestion=(
                "Use asyncio.gather() to run in parallel:\n"
                f"results = await asyncio.gather(\n"
                f"    call1(),\n"
                f"    call2()\n"
                f")"
            ),
            savings_monthly=savings,
            context={"await_count": len(await_nodes)}
        )
