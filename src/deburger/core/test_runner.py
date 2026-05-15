"""Test runner for executing pytest and parsing results."""

import subprocess
import re
import time
from pathlib import Path
from typing import Optional, List

from deburger.models.test_result import TestResult
from deburger.models.error import ErrorInfo
from deburger.core.parser import ErrorParser


class TestRunner:
    """Execute tests and parse results."""

    def __init__(self, test_runner: str = "pytest", timeout: int = 300):
        """
        Initialize test runner.

        Args:
            test_runner: Test runner to use (pytest or unittest)
            timeout: Maximum time for tests in seconds
        """
        self.test_runner = test_runner
        self.timeout = timeout
        self.parser = ErrorParser()

    def run_tests(
        self,
        test_path: Optional[str] = None,
        args: Optional[List[str]] = None
    ) -> TestResult:
        """
        Run tests and return results.

        Args:
            test_path: Path to specific test file or directory
            args: Additional arguments to pass to test runner

        Returns:
            TestResult with parsed errors
        """
        start_time = time.time()

        # Build command
        cmd = self._build_command(test_path, args)

        # Run tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=Path.cwd(),
            )
            output = result.stdout + result.stderr
            exit_code = result.returncode

        except subprocess.TimeoutExpired:
            return TestResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                output="Test execution timed out",
                duration=self.timeout,
            )
        except FileNotFoundError:
            return TestResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                output=f"Test runner '{self.test_runner}' not found",
                duration=0.0,
            )

        duration = time.time() - start_time

        # Parse output
        if self.test_runner == "pytest":
            return self._parse_pytest_output(output, duration, exit_code)
        else:
            return self._parse_unittest_output(output, duration, exit_code)

    def _build_command(
        self,
        test_path: Optional[str],
        args: Optional[List[str]]
    ) -> List[str]:
        """Build test command."""
        if self.test_runner == "pytest":
            cmd = ["pytest", "-v", "--tb=short"]
        else:
            cmd = ["python", "-m", "unittest"]

        if test_path:
            cmd.append(test_path)

        if args:
            cmd.extend(args)

        return cmd

    def _parse_pytest_output(
        self,
        output: str,
        duration: float,
        exit_code: int
    ) -> TestResult:
        """Parse pytest output."""
        # Extract test counts from summary line
        # Example: "5 passed, 2 failed, 1 skipped in 3.45s"
        summary_pattern = re.compile(
            r'(?:(\d+) passed)?.*?(?:(\d+) failed)?.*?(?:(\d+) skipped)?'
        )

        passed = 0
        failed = 0
        skipped = 0

        # Look for summary line
        for line in output.split('\n'):
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                match = summary_pattern.search(line)
                if match:
                    passed = int(match.group(1) or 0)
                    failed = int(match.group(2) or 0)
                    skipped = int(match.group(3) or 0)
                    break

        total = passed + failed + skipped

        # Parse errors if tests failed
        errors = []
        if failed > 0:
            errors = self.parser.parse_multiple(output)

        return TestResult(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            output=output,
        )

    def _parse_unittest_output(
        self,
        output: str,
        duration: float,
        exit_code: int
    ) -> TestResult:
        """Parse unittest output."""
        # Example: "Ran 10 tests in 2.345s"
        # "FAILED (failures=2, errors=1)"

        total_pattern = re.compile(r'Ran (\d+) test')
        failed_pattern = re.compile(r'failures=(\d+)')
        error_pattern = re.compile(r'errors=(\d+)')

        total = 0
        failed = 0
        errors_count = 0

        for line in output.split('\n'):
            total_match = total_pattern.search(line)
            if total_match:
                total = int(total_match.group(1))

            failed_match = failed_pattern.search(line)
            if failed_match:
                failed = int(failed_match.group(1))

            error_match = error_pattern.search(line)
            if error_match:
                errors_count = int(error_match.group(1))

        total_failed = failed + errors_count
        passed = total - total_failed

        # Parse errors
        errors = []
        if total_failed > 0:
            errors = self.parser.parse_multiple(output)

        return TestResult(
            total_tests=total,
            passed=passed,
            failed=total_failed,
            skipped=0,
            errors=errors,
            duration=duration,
            output=output,
        )

    def run_specific_tests(self, test_files: List[str]) -> TestResult:
        """
        Run specific test files.

        Args:
            test_files: List of test file paths

        Returns:
            Combined test results
        """
        all_results = []

        for test_file in test_files:
            result = self.run_tests(test_path=test_file)
            all_results.append(result)

        # Combine results
        return self._combine_results(all_results)

    def _combine_results(self, results: List[TestResult]) -> TestResult:
        """Combine multiple test results into one."""
        total_tests = sum(r.total_tests for r in results)
        passed = sum(r.passed for r in results)
        failed = sum(r.failed for r in results)
        skipped = sum(r.skipped for r in results)
        duration = sum(r.duration for r in results)

        all_errors = []
        for result in results:
            all_errors.extend(result.errors)

        combined_output = "\n\n".join(r.output for r in results)

        return TestResult(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=all_errors,
            duration=duration,
            output=combined_output,
        )
