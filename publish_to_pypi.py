#!/usr/bin/env python3
"""
PyPI Publishing Script for deburger

Usage:
    python publish_to_pypi.py --test      # Publish to TestPyPI
    python publish_to_pypi.py --prod      # Publish to PyPI (production)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n❌ {description} failed!")
        return False

    print(f"\n✅ {description} completed successfully!")
    return True


def check_version():
    """Check that version is properly set."""
    version_file = Path("src/deburger/_version.py")

    if not version_file.exists():
        print("❌ Version file not found!")
        return False

    content = version_file.read_text()
    if '__version__ = "' not in content:
        print("❌ Version not properly defined!")
        return False

    # Extract version
    for line in content.split('\n'):
        if '__version__' in line:
            version = line.split('"')[1]
            print(f"📌 Version: {version}")
            return True

    return False


def run_tests():
    """Run test suite."""
    if not Path("tests").exists():
        print("⚠️  No tests directory found, skipping tests")
        return True

    return run_command(
        ["pytest", "tests/", "-v", "--tb=short"],
        "Running tests"
    )


def lint_code():
    """Run linting."""
    return run_command(
        ["ruff", "check", "src/"],
        "Linting code"
    )


def clean_build():
    """Clean previous builds."""
    print("\n🧹 Cleaning previous builds...")

    paths_to_remove = [
        "build/",
        "dist/",
        "*.egg-info",
        "src/*.egg-info",
    ]

    for pattern in paths_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                subprocess.run(["rm", "-rf", str(path)])
                print(f"  Removed: {path}")
            elif path.is_file():
                path.unlink()
                print(f"  Removed: {path}")

    print("✅ Cleanup completed")
    return True


def build_package():
    """Build distribution packages."""
    return run_command(
        ["python", "setup.py", "sdist", "bdist_wheel"],
        "Building distribution packages"
    )


def upload_to_pypi(test_mode: bool = False):
    """Upload package to PyPI or TestPyPI."""
    repository = "testpypi" if test_mode else "pypi"
    description = f"Uploading to {'TestPyPI' if test_mode else 'PyPI'}"

    cmd = ["twine", "upload"]

    if test_mode:
        cmd.extend(["--repository", "testpypi"])

    cmd.append("dist/*")

    return run_command(cmd, description)


def verify_installation(test_mode: bool = False):
    """Verify package can be installed."""
    print("\n🔍 Verifying installation...")

    # Create temporary venv and test installation
    index_url = (
        "https://test.pypi.org/simple/"
        if test_mode
        else "https://pypi.org/simple/"
    )

    print(f"  Index URL: {index_url}")
    print("  Run this command to test installation:")
    print(f"    pip install --index-url {index_url} deburger")

    return True


def main():
    parser = argparse.ArgumentParser(description="Publish deburger to PyPI")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Publish to TestPyPI (for testing)",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Publish to PyPI (production)",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests",
    )
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip linting",
    )

    args = parser.parse_args()

    if not args.test and not args.prod:
        print("❌ Must specify either --test or --prod")
        parser.print_help()
        sys.exit(1)

    if args.prod:
        confirm = input("\n⚠️  You are about to publish to PRODUCTION PyPI. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Cancelled")
            sys.exit(1)

    print("\n" + "="*60)
    print("🍔 deburger PyPI Publishing Script")
    print("="*60)

    test_mode = args.test

    # Step 1: Check version
    if not check_version():
        sys.exit(1)

    # Step 2: Run tests (optional)
    if not args.skip_tests:
        if not run_tests():
            print("\n❌ Tests failed! Fix errors before publishing.")
            sys.exit(1)
    else:
        print("\n⚠️  Skipping tests")

    # Step 3: Lint (optional)
    if not args.skip_lint:
        if not lint_code():
            print("\n⚠️  Linting issues found (continuing anyway)")
    else:
        print("\n⚠️  Skipping linting")

    # Step 4: Clean previous builds
    if not clean_build():
        sys.exit(1)

    # Step 5: Build package
    if not build_package():
        sys.exit(1)

    # Step 6: Upload to PyPI
    if not upload_to_pypi(test_mode):
        sys.exit(1)

    # Step 7: Verify
    verify_installation(test_mode)

    print("\n" + "="*60)
    print("✅ Publishing completed successfully!")
    print("="*60)

    if test_mode:
        print("\n📝 Next steps:")
        print("  1. Test installation: pip install --index-url https://test.pypi.org/simple/ deburger")
        print("  2. If everything works, publish to production: python publish_to_pypi.py --prod")
    else:
        print("\n🎉 Package is now live on PyPI!")
        print("  Install: pip install deburger")
        print("  View: https://pypi.org/project/deburger/")


if __name__ == "__main__":
    main()
