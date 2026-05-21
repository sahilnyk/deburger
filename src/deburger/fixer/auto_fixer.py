"""Automatic security vulnerability fixer."""

import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from deburger.security.multi_language_scanner import Vulnerability


@dataclass
class Fix:
    """Represents a code fix."""

    file_path: str
    original_line: int
    original_code: str
    fixed_code: str
    description: str
    vulnerability_type: str


class AutoFixer:
    """Automatically fix common security vulnerabilities."""

    def __init__(self):
        self.fixers = {
            "hardcoded_secret": self._fix_hardcoded_secret,
            "code_injection": self._fix_code_injection,
            "command_injection": self._fix_command_injection,
            "xss": self._fix_xss,
            "sql_injection": self._fix_sql_injection,
        }

    def can_fix(self, vulnerability: Vulnerability) -> bool:
        """Check if vulnerability can be auto-fixed."""
        return vulnerability.type in self.fixers

    def generate_fix(self, vulnerability: Vulnerability) -> Optional[Fix]:
        """Generate fix for a vulnerability."""
        fixer = self.fixers.get(vulnerability.type)
        if not fixer:
            return None

        return fixer(vulnerability)

    def apply_fixes(self, fixes: List[Fix], dry_run: bool = False) -> int:
        """Apply fixes to files. Returns number of fixes applied."""
        if not fixes:
            return 0

        # Group fixes by file
        files_to_fix = {}
        for fix in fixes:
            if fix.file_path not in files_to_fix:
                files_to_fix[fix.file_path] = []
            files_to_fix[fix.file_path].append(fix)

        fixed_count = 0
        for file_path, file_fixes in files_to_fix.items():
            if dry_run:
                fixed_count += len(file_fixes)
                continue

            # Read file
            path = Path(file_path)
            if not path.exists():
                continue

            lines = path.read_text().splitlines()

            # Sort fixes by line number (reverse order to avoid offset issues)
            file_fixes.sort(key=lambda f: f.original_line, reverse=True)

            # Apply fixes
            for fix in file_fixes:
                if 0 <= fix.original_line - 1 < len(lines):
                    lines[fix.original_line - 1] = fix.fixed_code
                    fixed_count += 1

            # Write back
            path.write_text("\n".join(lines) + "\n")

        return fixed_count

    def _fix_hardcoded_secret(self, vuln: Vulnerability) -> Fix:
        """Fix hardcoded secrets by replacing with env vars."""
        code = vuln.code_snippet.strip()

        # Extract variable name and secret
        match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', code)
        if not match:
            return None

        var_name = match.group(1)

        # Generate env var name (uppercase)
        env_var = var_name.upper()

        # Generate fixed code based on language
        if vuln.language == "python":
            fixed = f'{var_name} = os.getenv("{env_var}")'
            # Add import if needed
            description = f'Replace hardcoded secret with os.getenv("{env_var}")'
        elif vuln.language == "javascript":
            fixed = f'const {var_name} = process.env.{env_var};'
            description = f'Replace hardcoded secret with process.env.{env_var}'
        else:
            # Generic replacement
            fixed = f'{var_name} = ENV["{env_var}"]'
            description = f'Replace hardcoded secret with environment variable'

        return Fix(
            file_path=vuln.file_path,
            original_line=vuln.line,
            original_code=code,
            fixed_code=fixed,
            description=description,
            vulnerability_type=vuln.type,
        )

    def _fix_code_injection(self, vuln: Vulnerability) -> Optional[Fix]:
        """Fix eval() usage."""
        code = vuln.code_snippet.strip()

        if vuln.language == "python":
            # Replace eval() with safer alternatives
            if "eval(" in code:
                # Try to determine if it's JSON or simple literals
                fixed = code.replace("eval(", "json.loads(")
                description = "Replace eval() with json.loads() - add 'import json' at top"
            else:
                return None
        elif vuln.language == "javascript":
            if "eval(" in code:
                fixed = code.replace("eval(", "JSON.parse(")
                description = "Replace eval() with JSON.parse()"
            else:
                return None
        else:
            return None

        return Fix(
            file_path=vuln.file_path,
            original_line=vuln.line,
            original_code=code,
            fixed_code=fixed,
            description=description,
            vulnerability_type=vuln.type,
        )

    def _fix_command_injection(self, vuln: Vulnerability) -> Optional[Fix]:
        """Fix command injection by removing shell=True."""
        code = vuln.code_snippet.strip()

        if "shell=True" in code:
            fixed = code.replace("shell=True", "shell=False")
            description = "Remove shell=True to prevent command injection"
        else:
            return None

        return Fix(
            file_path=vuln.file_path,
            original_line=vuln.line,
            original_code=code,
            fixed_code=fixed,
            description=description,
            vulnerability_type=vuln.type,
        )

    def _fix_xss(self, vuln: Vulnerability) -> Optional[Fix]:
        """Fix XSS by replacing innerHTML."""
        code = vuln.code_snippet.strip()

        if "innerHTML" in code:
            fixed = code.replace("innerHTML", "textContent")
            description = "Replace innerHTML with textContent to prevent XSS"
        else:
            return None

        return Fix(
            file_path=vuln.file_path,
            original_line=vuln.line,
            original_code=code,
            fixed_code=fixed,
            description=description,
            vulnerability_type=vuln.type,
        )

    def _fix_sql_injection(self, vuln: Vulnerability) -> Optional[Fix]:
        """Fix SQL injection - placeholder for now."""
        # SQL injection fixes are complex and context-dependent
        # Would need more sophisticated analysis
        return None
