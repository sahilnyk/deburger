"""Self-test command."""

import subprocess
import sys
from pathlib import Path

from deburger.ui.display import ui


def run_self_test():
    ui.header("Running self-tests")

    tests_dir = Path(__file__).parent.parent.parent.parent / "tests"

    if not tests_dir.exists():
        ui.error("Tests directory not found")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "-v"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            ui.success("All tests passed")
            return True
        else:
            ui.error("Some tests failed")
            ui.console.print(result.stdout)
            return False

    except FileNotFoundError:
        ui.warning("pytest not installed, running basic checks...")
        return _run_basic_checks()


def _run_basic_checks() -> bool:
    ui.info("Checking imports...")

    checks = [
        ("Security scanner", "from deburger.security.scanner import SecurityScanner"),
        ("Metrics calculator", "from deburger.metrics.calculator import MetricsCalculator"),
        ("Requirement tracker", "from deburger.requirements.tracker import RequirementTracker"),
        ("Decorators", "from deburger.decorators import deburger"),
        ("UI components", "from deburger.ui.display import ui"),
    ]

    all_passed = True
    for name, import_stmt in checks:
        try:
            exec(import_stmt)
            ui.success(f"{name}")
        except Exception as e:
            ui.error(f"{name}: {e}")
            all_passed = False

    return all_passed
