"""Main CLI entry point for deburger - Cloud Cost Analyzer."""

import sys
import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer(
    name="deburger",
    help="🍔 deburger - trim the fat from your cloud bill\n\nCatch expensive code before it hits production.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def init(
    provider: str = typer.Option("aws", "--provider", "-p", help="Cloud provider: aws, gcp, azure"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive setup wizard"),
):
    """
    Initialize deburger in current directory.

    Sets up cloud cost monitoring with your provider.

    Examples:
        deburger init --provider aws
        deburger init --provider gcp --interactive
    """
    from deburger.cli.init_command import run_init

    run_init(provider, interactive)


@app.command()
def check(
    path: str = typer.Argument(".", help="Path to analyze (default: changed files)"),
    provider: str = typer.Option(None, "--provider", "-p", help="Cloud provider to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis"),
):
    """
    Analyze code and predict cloud costs.

    Examples:
        deburger check                      # Check changed files
        deburger check src/                 # Check specific directory
        deburger check --provider aws -v    # Detailed AWS analysis
    """
    console.print("🍔 [bold cyan]analyzing code costs...[/bold cyan]\n")
    console.print("[yellow]check command coming soon![/yellow]")
    console.print("[dim]this will analyze your code and predict cloud costs[/dim]")


@app.command()
def diff(
    base: str = typer.Argument("main", help="Base branch/commit"),
    head: str = typer.Argument("HEAD", help="Target branch/commit"),
    provider: str = typer.Option(None, "--provider", "-p", help="Cloud provider"),
):
    """
    Compare costs between branches/commits.

    Examples:
        deburger diff main HEAD             # Compare main to current
        deburger diff main feature-branch   # Compare branches
        deburger diff HEAD~5 HEAD           # Last 5 commits
    """
    console.print("🍔 [bold cyan]comparing costs...[/bold cyan]\n")
    console.print(f"[dim]base:[/dim] {base}")
    console.print(f"[dim]head:[/dim] {head}")
    console.print("\n[yellow]diff command coming soon![/yellow]")


@app.command()
def optimize(
    path: str = typer.Argument(".", help="Path to optimize"),
    auto_apply: bool = typer.Option(False, "--auto-apply", help="Apply fixes automatically"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show fixes without applying"),
):
    """
    Find and fix expensive code patterns.

    Examples:
        deburger optimize                   # Show optimization suggestions
        deburger optimize --dry-run         # Preview fixes
        deburger optimize --auto-apply      # Apply all fixes
    """
    console.print("🍔 [bold cyan]finding optimizations...[/bold cyan]\n")
    console.print("[yellow]optimize command coming soon![/yellow]")
    console.print("[dim]this will auto-fix N+1 queries, over-provisioned resources, etc.[/dim]")


@app.command()
def watch(
    path: str = typer.Argument(".", help="Path to watch"),
    interval: float = typer.Option(5.0, "--interval", "-i", help="Check interval in seconds"),
):
    """
    Watch directory and analyze costs continuously.

    Examples:
        deburger watch                      # Watch current directory
        deburger watch src/ --interval 10   # Watch with 10s interval
    """
    from deburger.cli.watch_command import run_watch

    run_watch(path, interval)


@app.command()
def report(
    format: str = typer.Option("table", "--format", "-f", help="Format: table, json, html"),
    output: str = typer.Option(None, "--output", "-o", help="Save to file"),
    period: str = typer.Option("month", "--period", help="Period: day, week, month"),
):
    """
    Generate cost breakdown report.

    Examples:
        deburger report                     # Show table report
        deburger report --format json       # JSON output
        deburger report -f html -o report.html
    """
    console.print("🍔 [bold cyan]generating cost report...[/bold cyan]\n")
    console.print("[yellow]report command coming soon![/yellow]")
    console.print("[dim]this will show cost breakdown, trends, and savings[/dim]")


@app.command()
def leaderboard(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of developers to show"),
    period: str = typer.Option("month", "--period", "-p", help="Period: week, month, all"),
):
    """
    Show developer savings leaderboard.

    Examples:
        deburger leaderboard                # Top 10 this month
        deburger leaderboard -n 20          # Top 20
        deburger leaderboard --period week  # This week
    """
    console.print("🍔 [bold cyan]savings leaderboard[/bold cyan]\n")
    console.print("[yellow]leaderboard coming soon![/yellow]")
    console.print("[dim]track who's saving the most money[/dim]")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", help="Open config in editor"),
    validate: bool = typer.Option(False, "--validate", help="Validate configuration"),
):
    """
    Manage deburger configuration.

    Examples:
        deburger config --show              # Display config
        deburger config --edit              # Edit in editor
        deburger config --validate          # Check validity
    """
    from deburger.cli.config_command import run_config

    run_config(show, edit, validate)


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    clear: bool = typer.Option(False, "--clear", help="Clear all logs"),
):
    """
    View or manage logs.

    Examples:
        deburger logs                       # Last 50 lines
        deburger logs -n 100 --follow       # Live tail
        deburger logs --clear               # Clear logs
    """
    from deburger.cli.logs_command import run_logs

    run_logs(lines, follow, clear)


@app.command()
def version():
    """Show deburger version."""
    from deburger import __version__

    console.print(f"🍔 [cyan]deburger[/cyan] version [bold]{__version__}[/bold]")
    console.print("[dim]your cloud cost optimizer[/dim]")


def main():
    """Main entry point with error handling."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        console.print("\n[dim]run with --help for usage[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
