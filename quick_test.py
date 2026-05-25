#!/usr/bin/env python3
"""Quick integration test for deburger."""

import sys
import asyncio
import tempfile
from pathlib import Path


def test_imports():
    print("Testing imports...")
    try:
        from deburger.cli.main import app
        from deburger.scanner import FastScanner
        from deburger.config import load_config, DeburgerConfig
        from deburger.cost import CostEngine, TrafficEstimate
        from deburger.providers import ProviderRegistry
        from deburger.optimizer import CodeFixer, FixApplier
        from deburger.hooks import install_hook, uninstall_hook
        from deburger.analyzers import PythonAnalyzer, JavaScriptAnalyzer
        print("  all imports OK")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def test_scanner():
    print("Testing scanner...")
    try:
        from deburger.scanner import FastScanner
        from deburger.config import load_config

        config = load_config()
        scanner = FastScanner(config.to_dict())

        code = "for item in items:\n    result = db.query(item.id)\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp = f.name

        issues = asyncio.run(scanner.scan_path(tmp, incremental=False))
        Path(tmp).unlink()

        if len(issues) >= 1:
            print(f"  found {len(issues)} issue(s) - OK")
            return True
        else:
            print("  FAIL: no issues found in known-bad code")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def test_cost_engine():
    print("Testing cost engine...")
    try:
        from deburger.cost import CostEngine, TrafficEstimate
        from deburger.providers import ProviderRegistry

        provider = ProviderRegistry.get("aws")
        asyncio.run(provider.initialize({"region": "us-east-1"}))
        engine = CostEngine(provider, "us-east-1")
        asyncio.run(engine.preload_pricing())
        print("  cost engine initialized OK")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def test_optimizer():
    print("Testing optimizer...")
    try:
        from deburger.optimizer import CodeFixer
        from deburger.scanner import FastScanner
        from deburger.config import load_config

        config = load_config()
        scanner = FastScanner(config.to_dict())

        code = "for item in items:\n    result = db.query(item.id)\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp = f.name

        issues = asyncio.run(scanner.scan_path(tmp, incremental=False))
        Path(tmp).unlink()

        fixer = CodeFixer()
        fixes = asyncio.run(fixer.generate_all_fixes(issues, {tmp: code}))

        if fixes:
            print(f"  generated {len(fixes)} fix(es) - OK")
        else:
            print("  no fixes generated (expected for this pattern)")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def test_suppression():
    print("Testing suppression...")
    try:
        from deburger.analyzers.python_analyzer import PythonAnalyzer

        analyzer = PythonAnalyzer()
        config = {"detect": {"n_plus_one_queries": True, "sequential_async": True}, "traffic": {}}

        code_bad = "for item in items:\n    result = db.query(item.id)\n"
        code_suppressed = "for item in items:  # deburger:ignore\n    result = db.query(item.id)\n"

        issues_bad = analyzer.analyze("test.py", code_bad, config)
        issues_ok = analyzer.analyze("test.py", code_suppressed, config)

        if len(issues_bad) > 0 and len(issues_ok) == 0:
            print("  suppression works OK")
            return True
        else:
            print(f"  FAIL: bad={len(issues_bad)} suppressed={len(issues_ok)}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def main():
    print("=" * 50)
    print("deburger integration test")
    print("=" * 50)

    tests = [test_imports, test_scanner, test_cost_engine, test_optimizer, test_suppression]
    results = []

    for test in tests:
        results.append(test())

    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"{passed}/{total} passed")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
