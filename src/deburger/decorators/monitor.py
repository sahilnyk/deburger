"""Decorators for monitoring AI-generated code."""

import functools
import inspect
import time
from typing import Callable, Any

from deburger.security.scanner import SecurityScanner
from deburger.metrics.calculator import MetricsCalculator


def deburger(requirement: str = "", security: bool = True, track_metrics: bool = True):
    """
    Main deburger decorator to monitor function quality.

    Usage:
        @deburger(requirement="Handle user authentication", security=True)
        def login(username: str, password: str) -> bool:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            if security:
                _check_security(func)

            if track_metrics:
                _calculate_metrics(func)

            result = func(*args, **kwargs)

            execution_time = time.time() - start_time
            _log_execution(func.__name__, execution_time, requirement)

            return result

        wrapper.__deburger_requirement__ = requirement
        wrapper.__deburger_monitored__ = True

        return wrapper
    return decorator


def track_requirement(requirement: str):
    """
    Track if function implementation matches requirement.

    Usage:
        @track_requirement("Validate email format")
        def validate_email(email: str) -> bool:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            source = inspect.getsource(func)
            alignment = _check_requirement_alignment(requirement, source)

            if alignment < 0.7:
                print(f"⚠ Warning: {func.__name__} may not fully satisfy: {requirement}")
                print(f"  Alignment score: {alignment:.0%}")

            return result

        return wrapper
    return decorator


def security_check(fail_on_issues: bool = False):
    """
    Run security scan on function.

    Usage:
        @security_check(fail_on_issues=True)
        def process_user_input(data: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            source = inspect.getsource(func)
            scanner = SecurityScanner()
            vulns = scanner.scan_file(func.__code__.co_filename, source)

            if vulns:
                for vuln in vulns:
                    print(f"🔒 Security: {vuln.severity.value} - {vuln.description}")

                if fail_on_issues and any(v.severity.value == "HIGH" for v in vulns):
                    raise SecurityError(f"High severity vulnerabilities found in {func.__name__}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def _check_security(func: Callable) -> None:
    try:
        source = inspect.getsource(func)
        scanner = SecurityScanner()
        vulns = scanner.scan_file(func.__code__.co_filename, source)

        if vulns:
            print(f"⚠ {len(vulns)} security issues in {func.__name__}")
    except Exception:
        pass


def _calculate_metrics(func: Callable) -> None:
    try:
        source = inspect.getsource(func)
        calc = MetricsCalculator()
        metrics = calc.calculate(func.__code__.co_filename, source)

        if metrics.complexity > 10:
            print(f"⚠ High complexity ({metrics.complexity}) in {func.__name__}")
    except Exception:
        pass


def _check_requirement_alignment(requirement: str, source: str) -> float:
    req_words = set(requirement.lower().split())
    source_words = set(source.lower().split())

    overlap = len(req_words & source_words)
    return overlap / len(req_words) if req_words else 0.0


def _log_execution(func_name: str, execution_time: float, requirement: str) -> None:
    pass


class SecurityError(Exception):
    pass
