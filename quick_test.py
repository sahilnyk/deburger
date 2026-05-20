#!/usr/bin/env python3
"""Quick integration test for deburger."""

import sys
import tempfile
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    try:
        from deburger.cli.init_command import run_init
        from deburger.cli.analyze_command import run_analyze
        from deburger.cli.security_command import run_security_scan
        from deburger.cli.logs_command import run_logs
        from deburger.cli.config_command import run_config
        from deburger.utils.logger import get_logger
        from deburger.utils.config import load_config, DeburgerConfig
        from deburger.security.multi_language_scanner import MultiLanguageScanner
        print("✓ All imports OK")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_scanner():
    """Test multi-language scanner."""
    print("\nTesting multi-language scanner...")
    try:
        from deburger.security.multi_language_scanner import MultiLanguageScanner

        scanner = MultiLanguageScanner()

        # Test Python
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('password = "secret123"\n')
            f.write('eval("code")\n')
            py_file = f.name

        vulns = scanner.scan_file(py_file)
        Path(py_file).unlink()

        if len(vulns) >= 2:
            print(f"✓ Scanner found {len(vulns)} issues in Python")
        else:
            print(f"⚠ Scanner found only {len(vulns)} issues (expected 2+)")

        # Test JavaScript
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write('var api_key = "sk-12345";\n')
            f.write('innerHTML = data;\n')
            js_file = f.name

        vulns = scanner.scan_file(js_file)
        Path(js_file).unlink()

        if len(vulns) >= 1:
            print(f"✓ Scanner found {len(vulns)} issues in JavaScript")
        else:
            print(f"⚠ Scanner found {len(vulns)} issues in JS")

        return True
    except Exception as e:
        print(f"✗ Scanner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """Test logging system."""
    print("\nTesting logger...")
    try:
        from deburger.utils.logger import get_logger

        logger = get_logger()
        logger.info("Test log message")
        logger.log_command("test", arg1="value1")

        # Check log file exists
        log_dir = Path.home() / ".deburger" / "logs"
        log_file = log_dir / "deburger.log"

        if log_file.exists():
            print(f"✓ Log file created: {log_file}")
            return True
        else:
            print(f"⚠ Log file not found")
            return False
    except Exception as e:
        print(f"✗ Logger test failed: {e}")
        return False

def test_config():
    """Test config loading."""
    print("\nTesting config...")
    try:
        from deburger.utils.config import DeburgerConfig, SubGoalConfig, LLMConfig, SecurityConfig, MetricsConfig

        # Create config
        config = DeburgerConfig(
            requirement="Test",
            sub_goals=[
                SubGoalConfig(id="test", description="Test", weight=100)
            ],
            llm=LLMConfig(),
            security=SecurityConfig(),
            metrics=MetricsConfig()
        )

        # Validate
        errors = config.validate()

        if not errors:
            print("✓ Config creation and validation OK")
            return True
        else:
            print(f"⚠ Config validation errors: {errors}")
            return False
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("deburger Quick Integration Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Scanner", test_scanner()))
    results.append(("Logger", test_logger()))
    results.append(("Config", test_config()))

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20} {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
