import ast
import subprocess
from typing import Dict

from deburger.optimizer.fixer import Fix


class FixValidator:
    """validates fixes are syntactically correct before applying"""

    def validate_fix(self, fix: Fix) -> Dict:
        # check syntax is valid
        if fix.issue.file_path.endswith('.py'):
            return self._validate_python(fix)
        elif fix.issue.file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return self._validate_javascript(fix)

        return {"valid": True, "error": None}

    def _validate_python(self, fix: Fix) -> Dict:
        # parse fixed code as python
        try:
            ast.parse(fix.fixed_code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"syntax error in generated fix: {e.msg}",
                "line": e.lineno
            }

    def _validate_javascript(self, fix: Fix) -> Dict:
        # check if node is available for js validation
        try:
            result = subprocess.run(
                ["node", "--check", "-"],
                input=fix.fixed_code,
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                return {"valid": True, "error": None}
            else:
                return {
                    "valid": False,
                    "error": f"syntax error in generated fix: {result.stderr}",
                }
        except FileNotFoundError:
            # node not available, skip validation
            return {"valid": True, "error": None, "skipped": True}
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "validation timeout"}

    def validate_file_after_fix(self, file_path: str) -> Dict:
        # validate entire file after applying fix
        if file_path.endswith('.py'):
            return self._validate_python_file(file_path)
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return self._validate_javascript_file(file_path)

        return {"valid": True, "error": None}

    def _validate_python_file(self, file_path: str) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"file has syntax errors after fix: {e.msg}",
                "line": e.lineno
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _validate_javascript_file(self, file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ["node", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return {"valid": True, "error": None}
            else:
                return {
                    "valid": False,
                    "error": f"file has syntax errors after fix: {result.stderr}"
                }
        except FileNotFoundError:
            return {"valid": True, "error": None, "skipped": True}
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "validation timeout"}
