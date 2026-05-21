# 🧪 Testing Guide for deburger

This guide shows you how to test deburger in different ways.

---

## 📋 Table of Contents

1. [Unit Testing (Developer Tests)](#1-unit-testing-developer-tests)
2. [Integration Testing (Real Project Test)](#2-integration-testing-real-project-test)
3. [End-to-End Testing (Full Workflow)](#3-end-to-end-testing-full-workflow)
4. [Manual CLI Testing](#4-manual-cli-testing)
5. [CI/CD Testing](#5-cicd-testing)

---

## 1. Unit Testing (Developer Tests)

Test individual components in isolation.

### Setup

```bash
# Install deburger with dev dependencies
cd /path/to/deburger
pip install -e ".[dev,llm]"

# Or using make
make install-dev
```

### Run Unit Tests

```bash
# Run all tests with coverage
make test

# Or directly with pytest
pytest tests/ -v --cov=src/deburger --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_security_scanner.py -v

# Run specific test function
pytest tests/unit/test_parser.py::test_parse_basic_error -v

# Fast fail (stop on first failure)
pytest tests/ -x -v
```

### Current Test Coverage

```
tests/unit/
├── test_parser.py              # Error parsing tests
├── test_security_scanner.py    # Security vulnerability detection
├── test_metrics_calculator.py  # Code quality metrics
├── test_requirement_tracker.py # Progress tracking
└── test_test_runner.py         # Test execution
```

### Example: Writing a New Unit Test

```python
# tests/unit/test_new_feature.py
import pytest
from deburger.core.new_feature import NewFeature

@pytest.fixture
def feature():
    return NewFeature()

def test_basic_functionality(feature):
    """Test basic feature works correctly."""
    result = feature.process("input")
    assert result == "expected_output"

def test_handles_edge_case(feature):
    """Test edge case handling."""
    result = feature.process("")
    assert result is None
```

---

## 2. Integration Testing (Real Project Test)

Test deburger on a real project to ensure it works end-to-end.

### Method A: Test on Sample Project

```bash
# Create a test project
mkdir ~/test-deburger-project
cd ~/test-deburger-project

# Initialize git
git init
git config user.name "Test User"
git config user.email "test@example.com"

# Install deburger
pip install /path/to/deburger

# Initialize deburger
deburger init --requirement "Build a calculator app"

# Create sample Python file with issues
cat > calculator.py << 'EOF'
# calculator.py with intentional issues

password = "hardcoded123"  # Security issue

def divide(a, b):
    return a / b  # No validation - will fail on zero

def calculate(user_input):
    return eval(user_input)  # Code injection vulnerability
EOF

# Commit the file
git add calculator.py .deburger.yml
git commit -m "Add calculator with security issues"

# Run deburger analyze
deburger analyze

# Expected output: Should detect 3 security issues
# 1. Hardcoded secret (password)
# 2. Missing validation (divide by zero)
# 3. Code injection (eval)
```

### Method B: Test on Your Own Project

```bash
# Go to your project
cd /path/to/your/project

# Install deburger
pip install deburger

# Initialize
deburger init --requirement "Your project goal"

# Make a change
# ... edit some code ...

# Commit
git add .
git commit -m "Test change"

# Analyze
deburger analyze

# Expected: Progress metrics, security scan, quality score
```

---

## 3. End-to-End Testing (Full Workflow)

Test the complete deburger workflow from init to PR creation.

### E2E Test Script

```bash
#!/bin/bash
# e2e_test.sh - Full workflow test

set -e  # Exit on error

echo "🧪 Starting E2E test..."

# Setup
TEST_DIR=$(mktemp -d)
cd $TEST_DIR
git init
git config user.name "Test User"
git config user.email "test@example.com"

echo "📁 Test directory: $TEST_DIR"

# Step 1: Initialize deburger
echo "✓ Step 1: Initialize"
deburger init --requirement "Build REST API"

# Step 2: Create code with issues
echo "✓ Step 2: Create vulnerable code"
cat > api.py << 'EOF'
from flask import Flask, request
import subprocess

app = Flask(__name__)
SECRET_KEY = "my-secret-123"  # Issue 1: Hardcoded secret

@app.route("/search")
def search():
    query = request.args.get("q")
    result = eval(query)  # Issue 2: Code injection
    return {"result": result}

@app.route("/run")
def run_command():
    cmd = request.args.get("cmd")
    subprocess.run(cmd, shell=True)  # Issue 3: Command injection
    return {"status": "ok"}
EOF

git add .
git commit -m "Add API endpoints"

# Step 3: Analyze
echo "✓ Step 3: Analyze code"
deburger analyze > output.txt

# Step 4: Verify security issues detected
echo "✓ Step 4: Verify detection"
if grep -q "hardcoded_secret" output.txt && \
   grep -q "code_injection" output.txt && \
   grep -q "command_injection" output.txt; then
    echo "✅ All security issues detected!"
else
    echo "❌ Failed to detect security issues"
    cat output.txt
    exit 1
fi

# Step 5: Run security command
echo "✓ Step 5: Security scan"
deburger security

# Step 6: Fix issues
echo "✓ Step 6: Fix issues"
cat > api.py << 'EOF'
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")  # Fixed: Use env var

@app.route("/search")
def search():
    query = request.args.get("q", "")
    if not query or not query.isalnum():  # Fixed: Validate input
        return jsonify({"error": "Invalid query"}), 400
    return {"result": query}
EOF

git add api.py
git commit -m "Fix security issues"

# Step 7: Re-analyze
echo "✓ Step 7: Re-analyze"
deburger analyze > output2.txt

# Step 8: Verify issues fixed
if grep -q "No security issues" output2.txt || ! grep -q "HIGH" output2.txt; then
    echo "✅ Security issues fixed!"
else
    echo "⚠️  Some issues may remain"
fi

# Cleanup
echo "✓ Step 8: Cleanup"
cd /tmp
rm -rf $TEST_DIR

echo "✅ E2E test completed successfully!"
```

Run the E2E test:

```bash
chmod +x e2e_test.sh
./e2e_test.sh
```

---

## 4. Manual CLI Testing

Test each CLI command manually.

### Test Plan

```bash
# 1. Test: deburger init
deburger init --requirement "Test project"
# Expected: .deburger.yml created

# 2. Test: deburger config
deburger config
# Expected: Shows current configuration

# 3. Test: deburger analyze (with no commits)
deburger analyze
# Expected: "No commits to analyze" or similar message

# 4. Create test file and commit
echo "def test(): pass" > test.py
git add test.py .deburger.yml
git commit -m "Initial commit"

# 5. Test: deburger analyze (with commits)
deburger analyze
# Expected: Progress metrics, quality score

# 6. Test: deburger security
deburger security
# Expected: Security scan results

# 7. Test: deburger guide
deburger guide
# Expected: AI guidance prompt

# 8. Test: deburger report
deburger report
# Expected: Comprehensive metrics report

# 9. Test: deburger --help
deburger --help
# Expected: Help message with all commands

# 10. Test: Invalid command
deburger invalid-command
# Expected: Error message
```

### Test Checklist

- [ ] `deburger init` creates config file
- [ ] `deburger analyze` shows progress metrics
- [ ] `deburger security` detects vulnerabilities
- [ ] `deburger guide` generates guidance
- [ ] `deburger report` shows comprehensive metrics
- [ ] `deburger config` displays configuration
- [ ] `--help` works for all commands
- [ ] Error handling works (invalid inputs, missing files)

---

## 5. CI/CD Testing

Test deburger in automated pipelines.

### GitHub Actions Workflow

Create `.github/workflows/test-deburger.yml`:

```yaml
name: Test deburger

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install deburger
        run: |
          pip install -e ".[dev]"
      
      - name: Run unit tests
        run: |
          pytest tests/ -v --cov=src/deburger --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
      
      - name: Test CLI installation
        run: |
          deburger --help
      
      - name: Initialize test project
        run: |
          git config --global user.name "CI Test"
          git config --global user.email "ci@test.com"
          deburger init --requirement "CI test"
      
      - name: Test analyze command
        run: |
          echo "def test(): pass" > test.py
          git add test.py .deburger.yml
          git commit -m "Test commit"
          deburger analyze || true  # Don't fail on warnings
```

---

## 6. Testing Decorators

Test the runtime monitoring decorators.

```python
# test_decorators_manual.py
from deburger.decorators import deburger, security_check

@deburger(requirement="Test function", security=True)
@security_check(fail_on_issues=True)
def test_function(x: int) -> int:
    """Test function with deburger decorators."""
    return x * 2

if __name__ == "__main__":
    print("Testing decorators...")
    
    # Should pass
    result = test_function(5)
    assert result == 10
    print(f"✓ test_function(5) = {result}")
    
    print("✅ Decorator test passed!")
```

Run:
```bash
python test_decorators_manual.py
```

---

## 7. Test with Different Python Versions

```bash
# Using pyenv or virtualenv
for version in 3.9 3.10 3.11 3.12; do
    echo "Testing with Python $version"
    pyenv local $version
    python -m venv venv-$version
    source venv-$version/bin/activate
    pip install -e ".[dev]"
    pytest tests/ -v
    deactivate
done
```

---

## 8. Performance Testing

Test deburger on large codebases.

```bash
# Clone a large project
git clone https://github.com/django/django.git test-large-project
cd test-large-project

# Initialize deburger
deburger init --requirement "Test on large codebase"

# Time the analysis
time deburger analyze

# Expected: Should complete in reasonable time (<30s for Django)
```

---

## 9. Test Report Format

After running tests, check for:

```
✅ PASS Criteria:
- All unit tests pass
- Coverage > 80%
- No linting errors
- CLI commands work
- Security scanner detects known vulnerabilities
- Progress tracking calculates correctly
- Config file generation works

⚠️  WARNINGS:
- Performance > 30s on large projects
- Missing test coverage in new modules
- Flaky tests (random failures)

❌ FAIL Criteria:
- Any test failure
- Security vulnerabilities not detected
- CLI crashes on valid input
- Coverage < 70%
```

---

## 10. Quick Test Commands

```bash
# Quick smoke test
make test-fast

# Full test with coverage
make test

# Lint check
make lint

# Format code
make format

# Install and test CLI
make install && deburger --help

# Clean and rebuild
make clean && make build
```

---

## Common Issues & Fixes

### Issue: `deburger: command not found`
```bash
# Fix: Install in development mode
pip install -e .
# Or
make install
```

### Issue: `ModuleNotFoundError: No module named 'deburger'`
```bash
# Fix: Install package
pip install -e .
```

### Issue: Tests fail with `git not configured`
```bash
# Fix: Configure git
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Issue: `No coverage report`
```bash
# Fix: Install pytest-cov
pip install pytest-cov
```

---

## Summary

**Quick Test:**
```bash
make install-dev && make test
```

**Full Workflow Test:**
```bash
cd /tmp && mkdir test-project && cd test-project
git init
git config user.name "Test" && git config user.email "test@test.com"
deburger init --requirement "Test"
echo "password='secret'" > test.py
git add . && git commit -m "test"
deburger analyze
deburger security
```

**Expected Results:**
- Unit tests: All pass, >80% coverage
- Integration test: Detects hardcoded secret
- E2E test: Full workflow completes
- CLI: All commands work without crashes

🎯 **You now have multiple ways to test deburger thoroughly!**
