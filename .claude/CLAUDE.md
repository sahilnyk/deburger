---
description: Auto-Debug project guidelines for AI-powered debugging tool development
globs: "*.py, *.toml, *.yaml, *.md, tests/**"
alwaysApply: true
---

# Auto-Debug Project Guidelines

Auto-Debug is an AI-powered debugging tool that automatically detects, analyzes, fixes, and validates code errors. This is a **Python project** despite the presence of Bun guidelines in the directory.

## Technology Stack

### Core Technologies
- **Language:** Python 3.9+ (use type hints, dataclasses, async where appropriate)
- **Package Manager:** Poetry (NOT Bun, npm, or pip)
- **CLI Framework:** Typer with Rich for formatting
- **Testing:** pytest with pytest-cov
- **Formatting:** Black (line length: 100)
- **Linting:** Ruff (replaces flake8, isort, etc.)
- **Type Checking:** mypy in strict mode

### Key Dependencies
- `typer` - CLI framework
- `rich` - Terminal UI and formatting
- `pydantic` - Data validation and settings
- `openai` - OpenAI GPT-4 API
- `anthropic` - Anthropic Claude API
- `httpx` - Async HTTP client
- `GitPython` - Git operations
- `PyGithub` - GitHub API integration
- `structlog` - Structured logging
- `sqlite-utils` - SQLite database utilities

## Development Commands

```bash
# Installation
poetry install                    # Install dependencies
poetry add <package>              # Add new dependency
poetry add -D <package>           # Add dev dependency

# Development
poetry run pytest                 # Run tests
poetry run pytest -v --cov        # Run tests with coverage
poetry run mypy src/              # Type check
poetry run ruff check src/        # Lint code
poetry run black src/ tests/      # Format code
poetry run python -m auto_debug   # Run CLI locally

# Building
poetry build                      # Build wheel and sdist
poetry publish                    # Publish to PyPI

# Shell
poetry shell                      # Activate virtual env
```

## Code Style & Standards

### Python Style
- **Line length:** 100 characters
- **Imports:** Sorted with `ruff` (replaces isort)
- **Formatting:** Black (no configuration needed)
- **Docstrings:** Google style
- **Type hints:** Required for all functions

### Function Signatures
```python
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ErrorInfo:
    """Structured representation of a parsed error.
    
    Attributes:
        error_type: The type of exception (e.g., "TypeError")
        message: The error message
        file_path: Absolute path to the file where error occurred
        line_number: Line number where error occurred
    """
    error_type: str
    message: str
    file_path: str
    line_number: int

def parse_error(traceback: str, timeout: float = 5.0) -> Optional[ErrorInfo]:
    """Parse a Python traceback into structured error information.
    
    Args:
        traceback: Raw traceback string from test runner
        timeout: Maximum time to spend parsing (seconds)
        
    Returns:
        ErrorInfo object if parsing succeeds, None otherwise
        
    Raises:
        ParseError: If traceback format is unrecognized
    """
    pass
```

### Error Handling
```python
# Good: Specific exceptions with context
try:
    result = api_client.generate_fixes(error)
except APIError as e:
    logger.error("API call failed", error=str(e), error_id=error.id)
    raise FixGenerationError(f"Failed to generate fixes: {e}") from e

# Bad: Bare except or generic exceptions
try:
    result = api_client.generate_fixes(error)
except Exception:
    raise Exception("Something went wrong")
```

### Async/Await
Use async for I/O operations (API calls, file operations, database):
```python
import httpx

async def fetch_fix_from_api(error: ErrorInfo) -> List[Fix]:
    """Fetch fix candidates from AI API asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=build_request(error),
            timeout=30.0
        )
        return parse_response(response.json())
```

### Structured Logging
Always use structlog with structured fields:
```python
import structlog

logger = structlog.get_logger()

# Good: Structured fields
logger.info(
    "fix_generated",
    error_id=error.id,
    fix_count=3,
    confidence=0.95,
    duration_ms=1250
)

# Bad: String formatting
logger.info(f"Generated 3 fixes for {error.id} in 1250ms")
```

## Architecture Patterns

### Component Structure
```
src/auto_debug/
├── __init__.py
├── __main__.py              # CLI entry point
├── cli/                     # CLI commands
│   ├── __init__.py
│   ├── run.py              # Main run command
│   ├── config.py           # Config commands
│   └── logs.py             # Log commands
├── core/                    # Core business logic
│   ├── parser.py           # Error parsing
│   ├── classifier.py       # Error classification
│   ├── generator.py        # Fix generation
│   ├── validator.py        # Fix validation
│   └── tester.py           # Test runner
├── integrations/           # External integrations
│   ├── ai/                 # AI provider clients
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── ollama.py
│   ├── git.py              # Git operations
│   └── github.py           # GitHub API
├── storage/                # Data persistence
│   ├── cache.py            # Fix cache (SQLite)
│   └── logs.py             # Log storage
├── models/                 # Data models
│   ├── error.py            # ErrorInfo, ErrorClassification
│   ├── fix.py              # Fix, FixCandidate
│   └── config.py           # Config models
└── utils/                  # Utilities
    ├── async_utils.py
    ├── file_utils.py
    └── hash_utils.py
```

### Dependency Injection
Use dependency injection for testability:
```python
from typing import Protocol

class AIProvider(Protocol):
    """Protocol for AI providers."""
    async def generate_fixes(self, error: ErrorInfo) -> List[Fix]:
        ...

class FixGenerator:
    """Generates fix candidates using AI providers."""
    
    def __init__(self, providers: List[AIProvider]):
        self.providers = providers
    
    async def generate(self, error: ErrorInfo) -> List[Fix]:
        for provider in self.providers:
            try:
                return await provider.generate_fixes(error)
            except Exception as e:
                logger.warning("provider_failed", provider=provider, error=e)
        raise NoFixesGeneratedError("All providers failed")
```

## Testing Strategy

### Test Structure
```
tests/
├── unit/                   # Fast, isolated unit tests
│   ├── test_parser.py
│   ├── test_classifier.py
│   └── test_generator.py
├── integration/            # Integration tests (mocked APIs)
│   ├── test_fix_pipeline.py
│   └── test_github_integration.py
├── e2e/                    # End-to-end tests (real APIs)
│   └── test_full_workflow.py
└── fixtures/               # Test fixtures
    ├── errors/
    └── code_samples/
```

### Test Patterns
```python
import pytest
from unittest.mock import Mock, AsyncMock

# Unit test with mocking
@pytest.mark.asyncio
async def test_generate_fixes_success():
    # Arrange
    mock_client = AsyncMock()
    mock_client.generate_fixes.return_value = [
        Fix(id=1, code="x = 1", confidence=0.95)
    ]
    generator = FixGenerator([mock_client])
    error = ErrorInfo(error_type="TypeError", message="test", ...)
    
    # Act
    fixes = await generator.generate(error)
    
    # Assert
    assert len(fixes) == 1
    assert fixes[0].confidence == 0.95
    mock_client.generate_fixes.assert_called_once_with(error)

# Integration test with fixtures
@pytest.fixture
def sample_error():
    return ErrorInfo(
        error_type="ZeroDivisionError",
        message="division by zero",
        file_path="/path/to/file.py",
        line_number=42,
        code_context="result = x / y"
    )

def test_parse_pytest_error(sample_error):
    traceback = load_fixture("pytest_zero_division.txt")
    parsed = parse_error(traceback)
    assert parsed.error_type == sample_error.error_type
    assert parsed.line_number == sample_error.line_number
```

### Coverage Requirements
- **Overall:** >90% line coverage
- **Core modules:** >95% line coverage
- **Integration tests:** Cover happy path + major error cases
- **E2E tests:** At least 1 full workflow test

## Performance Guidelines

### Performance Targets
- Error parsing: <10ms
- Cache lookup: <1ms
- Fix generation (with API): <30s
- Test execution: Depends on suite size
- Log writing: <1ms overhead

### Optimization Patterns
```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=1000)
def compute_error_hash(error_type: str, message: str, context: str) -> str:
    """Compute hash for error caching. Results are memoized."""
    return hashlib.sha256(f"{error_type}:{message}:{context}".encode()).hexdigest()

# Use async for I/O
async def process_errors(errors: List[ErrorInfo]) -> List[Fix]:
    """Process multiple errors concurrently."""
    tasks = [generate_fix(error) for error in errors]
    return await asyncio.gather(*tasks)

# Lazy loading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auto_debug.integrations.github import GitHubClient

def create_pr(fix: Fix) -> None:
    """Create GitHub PR. Import delayed to avoid loading GitHub client at startup."""
    from auto_debug.integrations.github import GitHubClient
    client = GitHubClient()
    client.create_pr(fix)
```

## Security Guidelines

### Secrets Management
```python
# Good: Load from environment
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    github_token: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Bad: Hardcoded secrets
OPENAI_API_KEY = "sk-..."  # NEVER DO THIS
```

### Input Validation
```python
from pathlib import Path

def read_file_safely(file_path: str) -> str:
    """Read file with path validation to prevent directory traversal."""
    path = Path(file_path).resolve()
    
    # Ensure path is within project directory
    project_root = Path.cwd().resolve()
    if not path.is_relative_to(project_root):
        raise SecurityError(f"Path outside project: {path}")
    
    return path.read_text()
```

### Subprocess Safety
```python
import subprocess
import shlex

# Good: Use list form (no shell injection)
def run_tests(test_path: str) -> str:
    result = subprocess.run(
        ["pytest", "-v", test_path],
        capture_output=True,
        text=True,
        timeout=300
    )
    return result.stdout

# Bad: String form with shell=True
def run_tests_unsafe(test_path: str):
    cmd = f"pytest -v {test_path}"  # Vulnerable to injection!
    subprocess.run(cmd, shell=True)
```

## API Integration Guidelines

### Retry Logic
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_api_with_retry(client: httpx.AsyncClient, url: str) -> dict:
    """Call API with exponential backoff retry."""
    response = await client.post(url, timeout=30.0)
    response.raise_for_status()
    return response.json()
```

### Rate Limiting
```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, max_calls: int, period: timedelta):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    async def acquire(self):
        """Wait until rate limit allows next call."""
        now = datetime.now()
        self.calls = [t for t in self.calls if now - t < self.period]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + self.period - now).total_seconds()
            await asyncio.sleep(sleep_time)
            await self.acquire()
        
        self.calls.append(now)
```

## CLI Development

### Command Structure
```python
import typer
from rich.console import Console
from rich.progress import Progress

app = typer.Typer()
console = Console()

@app.command()
def run(
    test_path: str = typer.Argument(None, help="Path to test file or directory"),
    no_pr: bool = typer.Option(False, "--no-pr", help="Don't create PR"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show fixes without applying"),
):
    """Run tests and automatically debug failures."""
    with Progress() as progress:
        task = progress.add_task("[cyan]Running tests...", total=100)
        
        # Run workflow
        errors = run_tests(test_path)
        progress.update(task, advance=30)
        
        fixes = generate_fixes(errors)
        progress.update(task, advance=40)
        
        if not dry_run:
            apply_fixes(fixes)
        progress.update(task, advance=30)
    
    console.print("[green]✓[/green] Fixed 3 errors in 45s")
```

### Rich Formatting
```python
from rich.table import Table
from rich.panel import Panel

def display_fix_summary(fixes: List[Fix]):
    """Display fix summary with Rich formatting."""
    table = Table(title="Fix Summary")
    table.add_column("Error", style="red")
    table.add_column("Fix", style="green")
    table.add_column("Confidence", style="cyan")
    
    for fix in fixes:
        table.add_row(
            fix.error_type,
            fix.explanation[:50] + "...",
            f"{fix.confidence}%"
        )
    
    console.print(table)
```

## Documentation Standards

### Code Documentation
```python
def parse_error(traceback: str, timeout: float = 5.0) -> Optional[ErrorInfo]:
    """Parse a Python traceback into structured error information.
    
    This function extracts key information from pytest or unittest tracebacks,
    including file path, line number, error type, and surrounding code context.
    
    Args:
        traceback: Raw traceback string from test runner. Must be a valid Python
            traceback format (either pytest or unittest style).
        timeout: Maximum time to spend parsing in seconds. If parsing takes longer,
            returns None. Default is 5 seconds.
    
    Returns:
        ErrorInfo object containing structured error data if parsing succeeds,
        None if parsing times out or traceback format is invalid.
    
    Raises:
        ParseError: If traceback format is completely unrecognized (not just
            invalid, but not a Python traceback at all).
    
    Example:
        >>> traceback = '''
        ... Traceback (most recent call last):
        ...   File "test.py", line 5, in test_divide
        ...     result = divide(1, 0)
        ... ZeroDivisionError: division by zero
        ... '''
        >>> error = parse_error(traceback)
        >>> error.error_type
        'ZeroDivisionError'
    """
    pass
```

### README Structure
Every module should have a docstring explaining its purpose:
```python
"""Error parsing and classification module.

This module provides functions for parsing Python tracebacks from various test
runners (pytest, unittest, nose) into structured ErrorInfo objects. It also
classifies errors by complexity (low/medium/high) to guide fix generation.

Key components:
- parse_error(): Main parsing function
- classify_error(): Error complexity classifier
- extract_code_context(): Extract surrounding code lines

Example:
    from auto_debug.core.parser import parse_error
    
    traceback = get_test_output()
    error = parse_error(traceback)
    print(f"Error at {error.file_path}:{error.line_number}")
"""
```

## Git Workflow

### Branch Naming
- Feature: `feature/error-caching`
- Bugfix: `fix/parser-unicode-handling`
- Auto-generated: `auto-debug/fix-{error-type}-{hash}`

### Commit Messages
```
Format: <type>(<scope>): <subject>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- perf: Performance improvement
- style: Code style (formatting)
- chore: Build/tooling changes

Examples:
feat(parser): add support for pytest-xdist errors
fix(cache): handle corrupted cache gracefully
docs(cli): add examples for config commands
test(generator): add tests for multi-provider fallback
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Common Pitfalls to Avoid

### 1. Don't Silence Errors
```python
# Bad: Silent failures
try:
    fix = generate_fix(error)
except Exception:
    pass  # Error lost!

# Good: Log and propagate
try:
    fix = generate_fix(error)
except Exception as e:
    logger.error("fix_generation_failed", error_id=error.id, exception=str(e))
    raise
```

### 2. Don't Block on I/O
```python
# Bad: Blocking calls
def get_fixes(errors: List[ErrorInfo]) -> List[Fix]:
    return [api_client.generate(e) for e in errors]  # Sequential!

# Good: Concurrent I/O
async def get_fixes(errors: List[ErrorInfo]) -> List[Fix]:
    tasks = [api_client.generate(e) for e in errors]
    return await asyncio.gather(*tasks)  # Parallel!
```

### 3. Don't Leak Resources
```python
# Bad: Unclosed file/connection
def read_config():
    f = open("config.yaml")
    return yaml.safe_load(f)  # File never closed!

# Good: Context manager
def read_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)
```

### 4. Don't Trust User Input
```python
# Bad: Direct path usage
def analyze_file(path: str):
    return open(path).read()  # Path traversal vulnerability!

# Good: Validate first
def analyze_file(path: str):
    safe_path = Path(path).resolve()
    if not safe_path.is_relative_to(Path.cwd()):
        raise ValueError("Invalid path")
    return safe_path.read_text()
```

## CI/CD Configuration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Poetry
        run: pipx install poetry
      
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'poetry'
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests
        run: poetry run pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Environment Setup

### Required Tools
- Python 3.9+
- Poetry 1.7+
- Git 2.30+
- GitHub CLI (optional, for testing)

### Environment Variables
```bash
# .env.example
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...

# Optional
OLLAMA_BASE_URL=http://localhost:11434
AUTO_DEBUG_LOG_LEVEL=INFO
AUTO_DEBUG_CACHE_DIR=~/.auto-debug
```

### IDE Configuration (VSCode)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": false,
  "python.formatting.provider": "black",
  "python.analysis.typeCheckingMode": "strict",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "ruff.enable": true
}
```

---

## Summary

This is a **Python project** using modern best practices:
- Poetry for dependency management
- Typer + Rich for CLI
- pytest for testing
- Black + Ruff for code quality
- Structured logging with structlog
- Type hints everywhere
- Async/await for I/O operations

**Key Principles:**
1. Write simple, readable code
2. Use type hints for all functions
3. Test thoroughly (>90% coverage)
4. Log everything (structured)
5. Handle errors gracefully
6. Validate all inputs
7. Document clearly
8. Optimize for performance (caching, async)
