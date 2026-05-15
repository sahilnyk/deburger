"""Main CLI entry point for deburger."""

import asyncio
import typer
from rich.console import Console

app = typer.Typer(
    name="deburger",
    help="🍔 AI-powered debugging tool",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    test_path: str = typer.Argument(None, help="Path to test file or directory"),
    no_pr: bool = typer.Option(False, "--no-pr", help="Don't create PR"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show fixes without applying"),
):
    """Run tests and auto-debug failures."""
    from deburger.cli.run_command import run_debug_workflow

    asyncio.run(run_debug_workflow(
        test_path=test_path,
        dry_run=dry_run,
        no_pr=no_pr,
    ))


@app.command()
def config():
    """Configure deburger settings."""
    from deburger.cli.config_wizard import run_config_wizard

    run_config_wizard()


@app.command()
def version():
    """Show deburger version."""
    from deburger import __version__

    console.print(f"🍔 deburger v{__version__}")


if __name__ == "__main__":
    app()
