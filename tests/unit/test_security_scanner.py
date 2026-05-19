"""Tests for security scanner."""

import pytest

from deburger.security.scanner import SecurityScanner, Severity


def test_detect_eval_usage():
    scanner = SecurityScanner()
    code = """
def dangerous():
    user_input = input()
    result = eval(user_input)
    return result
"""
    vulns = scanner.scan_file("test.py", code)

    assert len(vulns) > 0
    eval_vulns = [v for v in vulns if v.type == "code_injection"]
    assert len(eval_vulns) == 1
    assert eval_vulns[0].severity == Severity.HIGH


def test_detect_hardcoded_password():
    scanner = SecurityScanner()
    code = """
password = "super_secret_123"
api_key = "sk-1234567890"
"""
    vulns = scanner.scan_file("test.py", code)

    assert len(vulns) == 2
    assert all(v.type == "hardcoded_secret" for v in vulns)
    assert all(v.severity == Severity.HIGH for v in vulns)


def test_detect_shell_injection():
    scanner = SecurityScanner()
    code = """
import subprocess
user_input = get_input()
subprocess.run(f"ls {user_input}", shell=True)
"""
    vulns = scanner.scan_file("test.py", code)

    shell_vulns = [v for v in vulns if v.type == "command_injection"]
    assert len(shell_vulns) >= 1
    assert shell_vulns[0].severity == Severity.HIGH


def test_clean_code_no_issues():
    scanner = SecurityScanner()
    code = """
def safe_function(x, y):
    return x + y
"""
    vulns = scanner.scan_file("test.py", code)

    assert len(vulns) == 0


def test_non_python_file_skipped():
    scanner = SecurityScanner()
    code = "console.log('hello');"
    vulns = scanner.scan_file("test.js", code)

    assert len(vulns) == 0
