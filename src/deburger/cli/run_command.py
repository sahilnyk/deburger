"""Main run command implementation."""

import asyncio
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from deburger.core.test_runner import TestRunner
from deburger.core.parser import ErrorParser
from deburger.core.classifier import ErrorClassifier
from deburger.core.fix_generator import FixGenerator
from deburger.integrations.openai_provider import OpenAIProvider
from deburger.storage.cache import FixCache
from deburger.models.error import ErrorInfo
from deburger.models.fix import Fix


console = Console()


async def run_debug_workflow(
    test_path: Optional[str] = None,
    dry_run: bool = False,
    no_pr: bool = False,
):
    """
    Run the full debug workflow.

    Args:
        test_path: Path to test file or directory
        dry_run: Show fixes without applying
        no_pr: Don't create PRs
    """
    console.print("\n🍔 [bold cyan]deburger[/bold cyan] v0.1.0\n")

    # Check for API key
    api_key = _get_api_key()
    if not api_key:
        console.print("[red]Error:[/red] No API key found")
        console.print("Run [cyan]deburger config[/cyan] to set up")
        return

    # Initialize components
    test_runner = TestRunner()
    classifier = ErrorClassifier()
    cache = FixCache()

    # Initialize AI provider
    provider = OpenAIProvider(api_key=api_key, model="gpt-4")
    fix_generator = FixGenerator(providers=[provider], cache=cache)

    # Run tests
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running tests...", total=None)

        result = test_runner.run_tests(test_path=test_path)

        progress.update(task, completed=True)

    if result.all_passed:
        console.print("\n[green]✓[/green] All tests passed! Nothing to fix.\n")
        return

    # Display test results
    console.print(f"\nFound [red]{result.failed}[/red] test failures\n")

    if not result.errors:
        console.print("[yellow]Warning:[/yellow] No errors could be parsed")
        return

    # Classify errors
    console.print("analyzing errors...\n")
    classifications = {}
    for error in result.errors:
        classification = classifier.classify(error)
        classifications[error.error_hash] = classification
        console.print(
            f"  [{_complexity_color(classification.complexity)}]{classification.complexity}[/] "
            f"{error.error_type} in [cyan]{error.function_name}[/cyan]"
        )

    console.print()

    # Generate fixes
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            "🔥 Generating fixes...",
            total=len(result.errors)
        )

        all_fixes = {}
        for i, error in enumerate(result.errors, 1):
            try:
                fixes = await fix_generator.generate(error)
                all_fixes[error.error_hash] = fixes

                # Check if from cache
                cached = len(fixes) == 1
                status = "from cache!" if cached else f"{len(fixes)} candidates"
                console.print(
                    f"  [{i}/{len(result.errors)}] "
                    f"[green]✓[/green] {error.error_type} - {status}"
                )

            except Exception as e:
                console.print(
                    f"  [{i}/{len(result.errors)}] "
                    f"[red]✗[/red] {error.error_type} - {str(e)}"
                )
                all_fixes[error.error_hash] = []

            progress.update(task, advance=1)

    console.print()

    # Display fixes
    _display_fixes(result.errors, all_fixes)

    if dry_run:
        console.print("\n[yellow]Dry run mode - no changes applied[/yellow]\n")
        return

    # Show next steps
    console.print()
    console.print(Panel.fit(
        "[bold green]Fixes generated![/bold green]\n\n"
        "Next steps:\n"
        "  • Review the suggested fixes above\n"
        "  • Apply fixes manually or run without --dry-run\n"
        "  • Run tests again to verify",
        border_style="green"
    ))
    console.print()


def _get_api_key() -> Optional[str]:
    """Get OpenAI API key from environment or config."""
    import os

    # Try environment variable first
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    # Try config file
    config_path = Path.cwd() / ".deburger.yaml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            providers = config.get("api", {}).get("providers", [])
            for provider in providers:
                if provider.get("name") == "openai":
                    key = provider.get("api_key", "")
                    # Handle ${VAR} syntax
                    if key.startswith("${") and key.endswith("}"):
                        var_name = key[2:-1]
                        return os.environ.get(var_name)
                    return key

    return None


def _complexity_color(complexity: str) -> str:
    """Get color for complexity level."""
    colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
    }
    return colors.get(complexity, "white")


def _display_fixes(errors: list[ErrorInfo], all_fixes: dict[str, list[Fix]]):
    """Display generated fixes in a table."""
    table = Table(title="Generated Fixes", show_lines=True)

    table.add_column("Error", style="red")
    table.add_column("Fix", style="green")
    table.add_column("Confidence", justify="right", style="cyan")

    for error in errors:
        fixes = all_fixes.get(error.error_hash, [])

        if not fixes:
            table.add_row(
                f"{error.error_type}\n{error.file_path}:{error.line_number}",
                "[red]No fix generated[/red]",
                "-"
            )
            continue

        # Show best fix
        best_fix = fixes[0]
        table.add_row(
            f"{error.error_type}\n{error.file_path}:{error.line_number}",
            f"{best_fix.explanation}\n\n{best_fix.reasoning}",
            f"{best_fix.confidence_percent}%"
        )

    console.print(table)
