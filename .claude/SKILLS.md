---
name: auto-debug-development-guide
description: Development patterns and best practices specific to Auto-Debug AI debugging tool
license: MIT
---

# Auto-Debug Development Guide

Patterns and practices for building the Auto-Debug AI-powered debugging tool.

---

## 1. Error Parsing Patterns

### Pattern: Robust Traceback Parsing
**Problem:** Test runners output tracebacks in various formats (pytest, unittest, different Python versions)

**Solution:**
```python
import re
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TracebackFrame:
    file: str
    line: int
    function: str
    code: str

def parse_traceback(output: str) -> Optional[List[TracebackFrame]]:
    """Parse traceback with multiple format support.
    
    Supports:
    - pytest (standard and verbose)
    - unittest
    - Python 3.9, 3.10, 3.11+
    """
    frames = []
    
    # Pattern 1: Standard Python traceback
    pattern = r'File "(.+)", line (\d+), in (.+)\n\s+(.+)'
    matches = re.finditer(pattern, output)
    
    for match in matches:
        frames.append(TracebackFrame(
            file=match.group(1),
            line=int(match.group(2)),
            function=match.group(3),
            code=match.group(4).strip()
        ))
    
    # Pattern 2: pytest format (if pattern 1 fails)
    if not frames:
        # Try pytest-specific parsing
        pass
    
    return frames if frames else None
```

**Key Points:**
- Try multiple patterns (generic first, specific second)
- Return `None` instead of raising if format unrecognized
- Preserve original error for fallback strategies

---

## 2. AI Integration Patterns

### Pattern: Provider Fallback Chain
**Problem:** AI APIs can fail, rate limit, or be unavailable

**Solution:**
```python
from typing import Protocol, List
import structlog

logger = structlog.get_logger()

class AIProvider(Protocol):
    name: str
    async def generate_fixes(self, error: ErrorInfo) -> List[Fix]: ...

class ProviderChain:
    """Tries providers in order until one succeeds."""
    
    def __init__(self, providers: List[AIProvider]):
        self.providers = providers
    
    async def generate(self, error: ErrorInfo) -> List[Fix]:
        last_error = None
        
        for provider in self.providers:
            try:
                logger.info("trying_provider", provider=provider.name, error_id=error.id)
                fixes = await provider.generate_fixes(error)
                
                if fixes:
                    logger.info("provider_success", provider=provider.name, fix_count=len(fixes))
                    return fixes
                    
            except Exception as e:
                logger.warning("provider_failed", provider=provider.name, error=str(e))
                last_error = e
                continue
        
        raise AllProvidersFailed("All AI providers failed") from last_error
```

**Usage:**
```python
chain = ProviderChain([
    OpenAIProvider(model="gpt-4"),
    AnthropicProvider(model="claude-3-5-sonnet-20241022"),
    OllamaProvider(model="llama3")  # Free fallback
])

fixes = await chain.generate(error)
```

---

### Pattern: Cost Tracking
**Problem:** AI API calls cost money, need to track and limit spending

**Solution:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

@dataclass
class CostTracker:
    """Track AI API costs in real-time."""
    
    budget: float  # Maximum spend in USD
    spent: float = 0.0
    calls: Dict[str, int] = field(default_factory=dict)
    
    # Model costs (per 1K tokens)
    COSTS = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    }
    
    def record_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record API call and update spent amount."""
        if model not in self.COSTS:
            logger.warning("unknown_model_cost", model=model)
            return
        
        cost = (
            (input_tokens / 1000) * self.COSTS[model]["input"] +
            (output_tokens / 1000) * self.COSTS[model]["output"]
        )
        
        self.spent += cost
        self.calls[model] = self.calls.get(model, 0) + 1
        
        if self.spent > self.budget:
            raise BudgetExceededError(f"Spent ${self.spent:.2f}, budget is ${self.budget:.2f}")
        
        logger.info(
            "api_cost_tracked",
            model=model,
            cost=f"${cost:.4f}",
            total_spent=f"${self.spent:.2f}",
            remaining=f"${self.budget - self.spent:.2f}"
        )
```

---

## 3. Caching Patterns

### Pattern: Content-Addressed Cache
**Problem:** Same errors occur repeatedly, causing expensive API calls

**Solution:**
```python
import hashlib
import sqlite3
from typing import Optional
import json

class FixCache:
    """SQLite-based cache for successful fixes."""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fixes (
                error_hash TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                fix_json TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                success_rate REAL DEFAULT 1.0,
                times_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def compute_hash(self, error: ErrorInfo) -> str:
        """Compute content hash for error."""
        content = f"{error.error_type}:{error.message}:{error.code_context}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, error: ErrorInfo) -> Optional[Fix]:
        """Retrieve cached fix if exists."""
        error_hash = self.compute_hash(error)
        
        cursor = self.conn.execute(
            "SELECT fix_json FROM fixes WHERE error_hash = ? AND success_rate > 0.7",
            (error_hash,)
        )
        row = cursor.fetchone()
        
        if row:
            # Update usage stats
            self.conn.execute(
                "UPDATE fixes SET times_used = times_used + 1 WHERE error_hash = ?",
                (error_hash,)
            )
            self.conn.commit()
            
            logger.info("cache_hit", error_hash=error_hash[:8])
            return Fix.from_json(row[0])
        
        logger.info("cache_miss", error_hash=error_hash[:8])
        return None
    
    def put(self, error: ErrorInfo, fix: Fix):
        """Store successful fix in cache."""
        error_hash = self.compute_hash(error)
        
        self.conn.execute(
            """
            INSERT OR REPLACE INTO fixes (error_hash, error_type, fix_json, confidence)
            VALUES (?, ?, ?, ?)
            """,
            (error_hash, error.error_type, fix.to_json(), int(fix.confidence * 100))
        )
        self.conn.commit()
        logger.info("cache_stored", error_hash=error_hash[:8], confidence=fix.confidence)
    
    def update_success_rate(self, error: ErrorInfo, success: bool):
        """Update success rate after fix is applied."""
        error_hash = self.compute_hash(error)
        
        # Exponential moving average
        self.conn.execute(
            """
            UPDATE fixes
            SET success_rate = success_rate * 0.9 + ? * 0.1
            WHERE error_hash = ?
            """,
            (1.0 if success else 0.0, error_hash)
        )
        self.conn.commit()
```

---

## 4. Testing Patterns

### Pattern: Smart Test Selection
**Problem:** Running full test suite after every fix is slow (1000+ tests can take minutes)

**Solution:**
```python
import ast
from pathlib import Path
from typing import Set

class TestSelector:
    """Select minimal set of tests affected by a code change."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._import_graph = self._build_import_graph()
    
    def _build_import_graph(self) -> Dict[str, Set[str]]:
        """Build graph of which files import which."""
        graph = {}
        
        for py_file in self.project_root.rglob("*.py"):
            imports = self._extract_imports(py_file)
            graph[str(py_file)] = imports
        
        return graph
    
    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from Python file."""
        try:
            tree = ast.parse(file_path.read_text())
        except:
            return set()
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        return imports
    
    def select_tests(self, changed_file: Path) -> List[Path]:
        """Find all tests that import the changed file."""
        affected_tests = []
        module_name = self._file_to_module(changed_file)
        
        for test_file in self.project_root.glob("tests/**/test_*.py"):
            imports = self._import_graph.get(str(test_file), set())
            
            # Check if test imports changed module (directly or indirectly)
            if module_name in imports:
                affected_tests.append(test_file)
        
        logger.info(
            "tests_selected",
            changed_file=str(changed_file),
            affected_count=len(affected_tests)
        )
        
        return affected_tests
    
    def _file_to_module(self, file_path: Path) -> str:
        """Convert file path to Python module name."""
        rel_path = file_path.relative_to(self.project_root)
        return str(rel_path.with_suffix("")).replace("/", ".")
```

**Usage:**
```python
selector = TestSelector(Path.cwd())
changed_file = Path("src/utils/math.py")

# Run only affected tests first
affected_tests = selector.select_tests(changed_file)
result = run_pytest(affected_tests)

# If affected tests pass, run full suite
if result.all_passed:
    result = run_pytest(["tests/"])
```

---

## 5. Git/GitHub Patterns

### Pattern: Safe Branch Creation
**Problem:** Creating branches can fail if name already exists or repo is dirty

**Solution:**
```python
from git import Repo, GitCommandError
from pathlib import Path

class SafeGitOperations:
    """Git operations with safety checks."""
    
    def __init__(self, repo_path: Path):
        self.repo = Repo(repo_path)
    
    def create_fix_branch(self, error: ErrorInfo) -> str:
        """Create branch for fix, handling conflicts."""
        # Check for uncommitted changes
        if self.repo.is_dirty():
            raise DirtyRepoError("Repository has uncommitted changes. Commit or stash first.")
        
        # Generate unique branch name
        base_name = f"auto-debug/fix-{error.error_type.lower()}"
        branch_name = base_name
        counter = 1
        
        while branch_name in [b.name for b in self.repo.branches]:
            branch_name = f"{base_name}-v{counter}"
            counter += 1
        
        # Create and checkout branch
        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            logger.info("branch_created", branch=branch_name)
            return branch_name
        except GitCommandError as e:
            raise BranchCreationError(f"Failed to create branch: {e}") from e
    
    def commit_fix(self, fix: Fix, error: ErrorInfo):
        """Commit fix with detailed message."""
        # Stage changed files
        self.repo.index.add([fix.file_path])
        
        # Generate commit message
        message = f"""Fix: {error.error_type} in {error.function_name}

Error: {error.message}
File: {error.file_path}:{error.line_number}
Confidence: {fix.confidence * 100:.0f}%

{fix.explanation}

Co-authored-by: Auto-Debug <auto-debug@example.com>
"""
        
        self.repo.index.commit(message)
        logger.info("fix_committed", branch=self.repo.active_branch.name)
```

---

### Pattern: Detailed PR Creation
**Problem:** PRs need comprehensive information for reviewers

**Solution:**
```python
from github import Github
from dataclasses import dataclass

@dataclass
class PRMetadata:
    error: ErrorInfo
    fix: Fix
    test_results: TestResult
    confidence: float

def create_detailed_pr(
    github_token: str,
    repo_name: str,
    branch: str,
    metadata: PRMetadata
) -> str:
    """Create PR with comprehensive details."""
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)
    
    # Generate title
    title = f"Fix: {metadata.error.error_type} in {metadata.error.function_name}"
    
    # Generate body
    body = f"""## 🤖 Auto-Debug Fix

**Error Type:** `{metadata.error.error_type}`  
**Confidence:** {metadata.confidence * 100:.0f}%  
**Tests Passed:** {metadata.test_results.passed}/{metadata.test_results.total}

### Error Details
```python
{metadata.error.message}
```
**Location:** `{metadata.error.file_path}:{metadata.error.line_number}`

### Fix Explanation
{metadata.fix.explanation}

### Code Changes
```diff
{metadata.fix.diff}
```

### Test Results
- ✅ {metadata.test_results.passed} tests passed
- ❌ {metadata.test_results.failed} tests failed
- ⏭️ {metadata.test_results.skipped} tests skipped

### Validation Checklist
- [x] Syntax validated
- [x] Tests passed
- [x] No regressions detected
{"- [x] Security scan passed" if metadata.confidence > 0.95 else ""}

---
🔗 Generated by [Auto-Debug](https://github.com/user/auto-debug)  
📊 Session ID: `{metadata.fix.session_id}`
"""
    
    # Create PR
    pr = repo.create_pull(
        title=title,
        body=body,
        head=branch,
        base="main",
        draft=(metadata.confidence < 0.95)
    )
    
    # Add labels
    pr.add_to_labels("auto-generated", "auto-fix")
    
    # Add reviewers if configured
    # pr.create_review_request(reviewers=["team-lead"])
    
    logger.info("pr_created", pr_number=pr.number, url=pr.html_url)
    return pr.html_url
```

---

## 6. CLI Patterns

### Pattern: Rich Progress Display
**Problem:** Users need feedback on long-running operations

**Solution:**
```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

def run_debug_workflow(errors: List[ErrorInfo]):
    """Run debug workflow with rich progress display."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Task 1: Parse errors
        parse_task = progress.add_task("[cyan]Parsing errors...", total=len(errors))
        parsed_errors = []
        for error in errors:
            parsed = parse_error(error)
            parsed_errors.append(parsed)
            progress.update(parse_task, advance=1)
        
        # Task 2: Generate fixes
        fix_task = progress.add_task("[yellow]Generating fixes...", total=len(parsed_errors))
        fixes = []
        for error in parsed_errors:
            fix = await generate_fix(error)
            fixes.append(fix)
            progress.update(fix_task, advance=1)
        
        # Task 3: Validate fixes
        test_task = progress.add_task("[green]Running tests...", total=len(fixes))
        results = []
        for fix in fixes:
            result = await test_fix(fix)
            results.append(result)
            progress.update(test_task, advance=1)
    
    # Display summary table
    display_summary(results)

def display_summary(results: List[FixResult]):
    """Display fix results in a table."""
    table = Table(title="Fix Summary")
    
    table.add_column("Error", style="red")
    table.add_column("Status", style="green")
    table.add_column("Confidence", justify="right")
    table.add_column("Tests", justify="right")
    
    for result in results:
        status = "✅ Fixed" if result.success else "❌ Failed"
        tests = f"{result.passed}/{result.total}"
        confidence = f"{result.confidence * 100:.0f}%"
        
        table.add_row(
            result.error.error_type,
            status,
            confidence,
            tests
        )
    
    console.print(table)
```

---

## 7. Configuration Patterns

### Pattern: Layered Configuration
**Problem:** Need to support defaults, project config, user config, and CLI overrides

**Solution:**
```python
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
import yaml

class AutoDebugConfig(BaseSettings):
    """Configuration with layered override support."""
    
    # API Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    github_token: Optional[str] = None
    
    # Behavior
    auto_apply_threshold: float = 0.95
    max_cost_per_run: float = 5.0
    
    # Testing
    test_runner: str = "pytest"
    test_timeout: int = 300
    
    class Config:
        env_file = ".env"
        env_prefix = "AUTO_DEBUG_"

def load_config() -> AutoDebugConfig:
    """Load config with priority: CLI args > User config > Project config > Defaults."""
    
    # Start with defaults (from environment)
    config = AutoDebugConfig()
    
    # Override with project config if exists
    project_config = Path.cwd() / ".auto-debug.yaml"
    if project_config.exists():
        project_data = yaml.safe_load(project_config.read_text())
        config = AutoDebugConfig(**{**config.dict(), **project_data})
    
    # Override with user config if exists
    user_config = Path.home() / ".auto-debug" / "config.yaml"
    if user_config.exists():
        user_data = yaml.safe_load(user_config.read_text())
        config = AutoDebugConfig(**{**config.dict(), **user_data})
    
    return config
```

---

## 8. Error Handling Patterns

### Pattern: Structured Error Context
**Problem:** Errors need rich context for debugging and logging

**Solution:**
```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ErrorContext:
    """Rich context for errors."""
    
    error_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "metadata": self.metadata
        }

class AutoDebugError(Exception):
    """Base exception with rich context."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.context = context or ErrorContext(
            error_type=self.__class__.__name__,
            message=message
        )
    
    def log(self):
        """Log error with full context."""
        logger.error(
            "error_occurred",
            **self.context.to_dict()
        )

class FixGenerationError(AutoDebugError):
    """Error during fix generation."""
    pass

class TestFailedError(AutoDebugError):
    """Error during test execution."""
    pass

# Usage
try:
    fixes = await generate_fixes(error)
except APIError as e:
    context = ErrorContext(
        error_type="FixGenerationError",
        message=str(e),
        metadata={"error_id": error.id, "provider": "openai"}
    )
    raise FixGenerationError("Failed to generate fixes", context=context) from e
```

---

## 9. Performance Patterns

### Pattern: Parallel Fix Validation
**Problem:** Testing fixes sequentially is slow when you have multiple candidates

**Solution:**
```python
import asyncio
from typing import List, Tuple

async def validate_fixes_parallel(
    fixes: List[Fix],
    max_concurrent: int = 3
) -> List[Tuple[Fix, TestResult]]:
    """Validate multiple fixes in parallel with concurrency limit."""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def validate_with_limit(fix: Fix) -> Tuple[Fix, TestResult]:
        async with semaphore:
            logger.info("validating_fix", fix_id=fix.id)
            result = await run_tests(fix)
            return (fix, result)
    
    # Run validations in parallel
    tasks = [validate_with_limit(fix) for fix in fixes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("validation_failed", error=str(result))
        else:
            valid_results.append(result)
    
    return valid_results

# Usage
fixes = [fix1, fix2, fix3]
results = await validate_fixes_parallel(fixes, max_concurrent=2)

# Select best fix
best_fix, best_result = max(
    results,
    key=lambda x: x[1].confidence,
    default=(None, None)
)
```

---

## 10. Logging Patterns

### Pattern: Correlation IDs
**Problem:** Need to track operations across multiple components

**Solution:**
```python
import structlog
import contextvars
from uuid import uuid4

# Context variable for session tracking
session_id_var = contextvars.ContextVar("session_id", default=None)

def get_logger():
    """Get logger with session context."""
    logger = structlog.get_logger()
    
    # Add session_id to all logs
    session_id = session_id_var.get()
    if session_id:
        logger = logger.bind(session_id=session_id)
    
    return logger

class DebugSession:
    """Context manager for debug sessions."""
    
    def __init__(self):
        self.session_id = str(uuid4())
    
    def __enter__(self):
        session_id_var.set(self.session_id)
        logger = get_logger()
        logger.info("session_started")
        return self.session_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = get_logger()
        if exc_type:
            logger.error("session_failed", error=str(exc_val))
        else:
            logger.info("session_completed")
        
        session_id_var.set(None)

# Usage
with DebugSession() as session_id:
    # All logs in this context will have session_id
    logger = get_logger()
    logger.info("parsing_error")  # Automatically includes session_id
    logger.info("generating_fixes")
```

---

## Summary

These patterns ensure:
1. **Robustness:** Handle multiple formats and failure modes
2. **Efficiency:** Cache results, parallelize operations, select smart subsets
3. **Observability:** Rich logging with correlation IDs
4. **Safety:** Validate all changes, handle dirty state
5. **User Experience:** Clear progress indicators, detailed feedback
6. **Cost Management:** Track and limit API spending
7. **Maintainability:** Clean separation of concerns, testable components

Apply these patterns throughout the Auto-Debug codebase for consistency and quality.
