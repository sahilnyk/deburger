"""Multi-language security scanner with pattern-based detection."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from pathlib import Path


class Severity(Enum):
    """Vulnerability severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Vulnerability:
    """Security vulnerability finding."""

    type: str
    severity: Severity
    line: int
    column: int
    description: str
    code_snippet: str
    file_path: str
    language: str
    fix_suggestion: Optional[str] = None
    cwe_id: Optional[str] = None


class MultiLanguageScanner:
    """Security scanner supporting multiple programming languages."""

    def __init__(self):
        self.patterns = self._init_patterns()

    def _init_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize security patterns for all languages."""
        return {
            "python": [
                {
                    "pattern": r"\beval\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "Use of eval() can execute arbitrary code",
                    "fix": "Use ast.literal_eval() or json.loads() instead",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"\bexec\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "Use of exec() can execute arbitrary code",
                    "fix": "Avoid exec() or use restricted execution environment",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"subprocess\.(run|call|Popen).*shell\s*=\s*True",
                    "type": "command_injection",
                    "severity": Severity.HIGH,
                    "description": "shell=True can lead to command injection",
                    "fix": "Use shell=False and pass arguments as list",
                    "cwe": "CWE-78",
                },
                {
                    "pattern": r"(password|passwd|pwd|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded secret/credential detected",
                    "fix": "Use environment variables or secure vault",
                    "cwe": "CWE-798",
                },
                {
                    "pattern": r"pickle\.loads?\(",
                    "type": "unsafe_deserialization",
                    "severity": Severity.HIGH,
                    "description": "pickle can execute arbitrary code during deserialization",
                    "fix": "Use json or safer serialization format",
                    "cwe": "CWE-502",
                },
            ],
            "javascript": [
                {
                    "pattern": r"\beval\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "eval() executes arbitrary JavaScript code",
                    "fix": "Use JSON.parse() or safer alternatives",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"innerHTML\s*=",
                    "type": "xss",
                    "severity": Severity.HIGH,
                    "description": "innerHTML can lead to XSS vulnerabilities",
                    "fix": "Use textContent or sanitize input",
                    "cwe": "CWE-79",
                },
                {
                    "pattern": r"(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded secret/credential detected",
                    "fix": "Use environment variables",
                    "cwe": "CWE-798",
                },
                {
                    "pattern": r"dangerouslySetInnerHTML",
                    "type": "xss",
                    "severity": Severity.HIGH,
                    "description": "dangerouslySetInnerHTML can introduce XSS",
                    "fix": "Sanitize HTML or use safe rendering methods",
                    "cwe": "CWE-79",
                },
            ],
            "typescript": [
                {
                    "pattern": r"\beval\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "eval() executes arbitrary code",
                    "fix": "Use safer alternatives like JSON.parse()",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded secret detected",
                    "fix": "Use environment variables",
                    "cwe": "CWE-798",
                },
            ],
            "go": [
                {
                    "pattern": r"exec\.Command.*\$",
                    "type": "command_injection",
                    "severity": Severity.HIGH,
                    "description": "Command execution with variable interpolation",
                    "fix": "Validate and sanitize command arguments",
                    "cwe": "CWE-78",
                },
                {
                    "pattern": r"(password|secret|apiKey|token)\s*:=\s*\"[^\"]{8,}\"",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded secret detected",
                    "fix": "Use environment variables or secrets manager",
                    "cwe": "CWE-798",
                },
            ],
            "java": [
                {
                    "pattern": r"Runtime\.getRuntime\(\)\.exec",
                    "type": "command_injection",
                    "severity": Severity.HIGH,
                    "description": "Runtime.exec() can lead to command injection",
                    "fix": "Validate input and use ProcessBuilder",
                    "cwe": "CWE-78",
                },
                {
                    "pattern": r"(password|secret|apiKey)\s*=\s*\"[^\"]{8,}\"",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded credential detected",
                    "fix": "Use properties file or environment variables",
                    "cwe": "CWE-798",
                },
            ],
            "ruby": [
                {
                    "pattern": r"\beval\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "eval() executes arbitrary Ruby code",
                    "fix": "Avoid eval() or use safer alternatives",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"system\(.*\$",
                    "type": "command_injection",
                    "severity": Severity.HIGH,
                    "description": "system() with variable interpolation",
                    "fix": "Use array form of system() or validate input",
                    "cwe": "CWE-78",
                },
            ],
            "php": [
                {
                    "pattern": r"\beval\s*\(",
                    "type": "code_injection",
                    "severity": Severity.CRITICAL,
                    "description": "eval() executes arbitrary PHP code",
                    "fix": "Avoid eval() entirely",
                    "cwe": "CWE-95",
                },
                {
                    "pattern": r"(mysqli_query|mysql_query).*\$",
                    "type": "sql_injection",
                    "severity": Severity.CRITICAL,
                    "description": "SQL query with variable interpolation",
                    "fix": "Use prepared statements",
                    "cwe": "CWE-89",
                },
            ],
            "sql": [
                {
                    "pattern": r"(password|passwd)\s*=\s*'[^']{8,}'",
                    "type": "hardcoded_secret",
                    "severity": Severity.CRITICAL,
                    "description": "Hardcoded password in SQL",
                    "fix": "Use parameterized queries",
                    "cwe": "CWE-798",
                },
            ],
        }

    def scan_file(self, file_path: str) -> List[Vulnerability]:
        """Scan a file for security vulnerabilities."""
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return []

        language = self._detect_language(file_path)
        if not language:
            return []

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        return self._scan_content(content, file_path, language)

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".sql": "sql",
        }

        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext)

    def _scan_content(
        self, content: str, file_path: str, language: str
    ) -> List[Vulnerability]:
        """Scan file content for vulnerabilities."""
        vulnerabilities = []
        patterns = self.patterns.get(language, [])

        lines = content.split("\n")

        for pattern_def in patterns:
            pattern = re.compile(pattern_def["pattern"], re.IGNORECASE | re.MULTILINE)

            for line_num, line in enumerate(lines, start=1):
                matches = pattern.finditer(line)

                for match in matches:
                    vuln = Vulnerability(
                        type=pattern_def["type"],
                        severity=pattern_def["severity"],
                        line=line_num,
                        column=match.start() + 1,
                        description=pattern_def["description"],
                        code_snippet=line.strip()[:100],
                        file_path=file_path,
                        language=language,
                        fix_suggestion=pattern_def.get("fix"),
                        cwe_id=pattern_def.get("cwe"),
                    )
                    vulnerabilities.append(vuln)

        return vulnerabilities

    def scan_directory(
        self, directory: str, recursive: bool = True, ignore_patterns: List[str] = None
    ) -> List[Vulnerability]:
        """Scan entire directory for vulnerabilities."""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return []

        ignore_patterns = ignore_patterns or []
        vulnerabilities = []

        pattern = "**/*" if recursive else "*"
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                # Check if file should be ignored
                should_ignore = any(
                    re.search(pattern, str(file_path)) for pattern in ignore_patterns
                )

                if not should_ignore:
                    vulns = self.scan_file(str(file_path))
                    vulnerabilities.extend(vulns)

        return vulnerabilities

    def filter_by_severity(
        self, vulnerabilities: List[Vulnerability], min_severity: Severity
    ) -> List[Vulnerability]:
        """Filter vulnerabilities by minimum severity."""
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }

        min_level = severity_order[min_severity]

        return [
            v for v in vulnerabilities if severity_order[v.severity] >= min_level
        ]
