# Contributing to deburger

Thanks for your interest in contributing to deburger!

## Development Setup

```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
poetry install
```

## Running Tests

```bash
poetry run pytest
poetry run pytest --cov
```

## Code Quality

We use deburger to monitor its own code quality:

```bash
deburger analyze
deburger security
```

Before submitting a PR:

1. Run tests: `pytest`
2. Check types: `mypy src/`
3. Lint: `ruff check src/`
4. Format: `black src/ tests/`
5. Run deburger: `deburger analyze`

## Commit Guidelines

Use conventional commits:

- `added: new feature`
- `fixed: bug description`
- `refactored: code improvement`
- `updated: documentation`

Keep commits small (5-10 words).

## Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run quality checks
4. Commit with descriptive message
5. Push and create PR
6. Ensure CI passes

## Code Standards

- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions under 50 lines
- Maintain cyclomatic complexity < 10
- No hardcoded secrets or credentials
- Validate all user input
- Write tests for new features

## Architecture

```
src/deburger/
├── analyzer/       # Code change analysis
├── security/       # Vulnerability scanning
├── metrics/        # Quality metrics
├── requirements/   # Progress tracking
├── guidance/       # AI steering
├── testing/        # Test generation
├── llm/           # LLM integration
└── cli/           # CLI commands
```

## Adding New Features

1. Discuss in an issue first
2. Write tests before implementation
3. Keep changes focused and minimal
4. Update documentation
5. Run deburger to ensure quality

## Security

Report security issues to: sahilnayak2056@gmail.com

Do not open public issues for security vulnerabilities.

## Questions?

Open an issue or discussion on GitHub.
