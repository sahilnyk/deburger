# Contributing to 🍔 deburger

Thanks for contributing!

## Setup

```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
pip install -e ".[dev]"
```

## Run Tests

```bash
pytest
pytest --cov
```

## Code Quality

```bash
ruff check src/
mypy src/
black src/ tests/
```

## Commit Guidelines

Keep commits clean:

```bash
git add src/deburger/security/
git commit -m "added: XSS detection"

git add src/deburger/metrics/
git commit -m "fixed: complexity calculation"
```

Format: `added:` / `fixed:` / `refactored:` / `updated:` (5-6 words max)

## Before PR

1. Run tests: `pytest`
2. Check types: `mypy src/`
3. Lint: `ruff check src/`
4. Format: `black src/`

## Code Standards

- Type hints for functions
- Docstrings for public APIs
- Functions under 50 lines
- Complexity under 10
- No hardcoded secrets
- Validate all input

## Questions?

Open an issue or discussion.
