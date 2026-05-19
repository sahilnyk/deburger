"""Security vulnerability scanner using AST and pattern matching."""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Vulnerability:
    type: str
    severity: Severity
    line: int
    description: str
    code_snippet: str
    fix_suggestion: Optional[str] = None


class SecurityScanner:
    def __init__(self):
        self.patterns = self._load_patterns()

    def scan_file(self, filepath: str, content: str) -> list[Vulnerability]:
        if not filepath.endswith(".py"):
            return []

        vulns = []
        vulns.extend(self._scan_ast(content))
        vulns.extend(self._scan_patterns(content))
        return vulns

    def _scan_ast(self, content: str) -> list[Vulnerability]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        vulns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    if node.func.id == "eval":
                        vulns.append(
                            Vulnerability(
                                type="code_injection",
                                severity=Severity.HIGH,
                                line=node.lineno,
                                description="Use of eval() can execute arbitrary code",
                                code_snippet="eval(...)",
                                fix_suggestion="Use ast.literal_eval() for safe evaluation",
                            )
                        )
                    elif node.func.id == "exec":
                        vulns.append(
                            Vulnerability(
                                type="code_injection",
                                severity=Severity.HIGH,
                                line=node.lineno,
                                description="Use of exec() can execute arbitrary code",
                                code_snippet="exec(...)",
                                fix_suggestion="Avoid exec() or use restricted execution",
                            )
                        )

                if hasattr(node.func, "attr"):
                    if node.func.attr == "format" and self._is_sql_context(node):
                        vulns.append(
                            Vulnerability(
                                type="sql_injection",
                                severity=Severity.HIGH,
                                line=node.lineno,
                                description="String formatting in SQL query can lead to injection",
                                code_snippet="query.format(...)",
                                fix_suggestion="Use parameterized queries",
                            )
                        )

        return vulns

    def _scan_patterns(self, content: str) -> list[Vulnerability]:
        vulns = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if re.search(r"password\s*=\s*['\"][\w]+['\"]", line, re.I):
                vulns.append(
                    Vulnerability(
                        type="hardcoded_secret",
                        severity=Severity.HIGH,
                        line=i,
                        description="Hardcoded password found",
                        code_snippet=line.strip(),
                        fix_suggestion="Use environment variables",
                    )
                )

            if re.search(r"api[_-]?key\s*=\s*['\"][\w-]+['\"]", line, re.I):
                vulns.append(
                    Vulnerability(
                        type="hardcoded_secret",
                        severity=Severity.HIGH,
                        line=i,
                        description="Hardcoded API key found",
                        code_snippet=line.strip(),
                        fix_suggestion="Use environment variables",
                    )
                )

            if "random.random()" in line and any(
                word in line.lower() for word in ["token", "key", "password", "secret"]
            ):
                vulns.append(
                    Vulnerability(
                        type="weak_random",
                        severity=Severity.MEDIUM,
                        line=i,
                        description="Insecure random for security-sensitive operation",
                        code_snippet=line.strip(),
                        fix_suggestion="Use secrets module for cryptographic randomness",
                    )
                )

            if re.search(r"subprocess\.(call|run|Popen)\(.*shell\s*=\s*True", line):
                vulns.append(
                    Vulnerability(
                        type="command_injection",
                        severity=Severity.HIGH,
                        line=i,
                        description="Shell injection risk with shell=True",
                        code_snippet=line.strip(),
                        fix_suggestion="Use shell=False with list arguments",
                    )
                )

        return vulns

    def _is_sql_context(self, node: ast.Call) -> bool:
        return False

    def _load_patterns(self) -> dict:
        return {}
