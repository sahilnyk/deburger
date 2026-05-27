# Contributing to deburger

## Quick Start

```bash
git clone https://github.com/sahilnyk/deburger
cd deburger
pip install -e ".[dev]"
pytest
```

## Development Setup

**Requirements:**
- Python 3.9+
- pip

**Install development dependencies:**
```bash
pip install -e ".[dev]"
```

This installs deburger in editable mode plus:
- pytest (testing)
- pytest-cov (coverage)
- mypy (type checking)
- ruff (linting)
- black (formatting)

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write Code

Follow the existing code style:
- Type hints for all functions
- Docstrings for public APIs
- No `eval()` or `exec()`
- No `shell=True` in subprocess

### 3. Add Tests

Every feature needs tests:

```bash
# Add tests to tests/unit/
pytest tests/unit/test_your_feature.py
```

Aim for >80% coverage on new code.

### 4. Run Checks

```bash
# Run tests
pytest

# Check types
mypy src/

# Lint code
ruff check src/

# Format code
black src/ tests/
```

### 5. Commit

```bash
git add .
git commit -m "feat: add new pattern detector for X"
```

**Commit format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Adding tests
- `refactor:` Code refactoring

## Adding New Features

### New Pattern Detector

1. Create file in `src/deburger/analyzers/patterns/`
2. Inherit from `PatternDetector`
3. Implement `detect()` method
4. Add to `ALL_PATTERNS` in `__init__.py`
5. Add tests in `tests/unit/`

Example:

```python
from deburger.analyzers.patterns.base import PatternDetector

class MyPatternDetector(PatternDetector):
    def detect(self, node, context):
        # Your detection logic
        if is_expensive_pattern(node):
            return Issue(
                type=IssueType.MY_PATTERN,
                severity=Severity.HIGH,
                line_number=node.lineno,
                description="Description of issue",
                fix_suggestion="How to fix it"
            )
        return None
```

### New Cloud Provider

1. Create file in `src/deburger/providers/`
2. Inherit from `BaseProvider`
3. Implement pricing methods
4. Register in `ProviderRegistry`
5. Add tests

### New Language Support

1. Create analyzer in `src/deburger/analyzers/`
2. Implement parsing logic
3. Register in `AnalyzerRegistry`
4. Add pattern detection
5. Add tests with sample code

## Testing

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=src/deburger --cov-report=html
```

**Run specific test:**
```bash
pytest tests/unit/test_parser.py::test_detect_s3_in_loop
```

**Test structure:**
- `tests/unit/` - Fast, isolated unit tests
- `tests/integration/` - Integration tests with mocked APIs

## Code Style

We use:
- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking (strict mode)

Run before committing:
```bash
black src/ tests/
ruff check src/ --fix
mypy src/
```

## Pull Requests

1. Fork the repository
2. Create your feature branch
3. Make your changes with tests
4. Ensure all checks pass
5. Push to your fork
6. Open a Pull Request

**PR Guidelines:**
- Describe what changes and why
- Reference any related issues
- Include test results
- Keep PRs focused (one feature per PR)

## Reporting Bugs

Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, deburger version)
- Sample code if applicable

## Suggesting Features

Open an issue with:
- Clear use case
- Why this would be valuable
- Proposed implementation (optional)

## Questions?

- Open a discussion on GitHub
- Check existing issues
- Review the code (it's well-documented)
