"""Main CLI entry point for deburger."""

import sys
import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer(
    name="deburger",
    help="🍔 deburger - catch bugs before they catch you\n\nMonitor AI-generated code quality, security, and progress tracking.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def init(
    requirement: str = typer.Argument(None, help="Main project requirement/goal"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive setup wizard"),
):
    """
    Initialize deburger in current directory.

    Creates .deburger.yml configuration file.

    Examples:
        deburger init "Build REST API with authentication"
        deburger init --interactive
    """
    from deburger.cli.init_command import run_init

    if not requirement and not interactive:
        console.print("[red]Error:[/red] Provide a requirement or use --interactive")
        console.print("\nExample: deburger init \"Build REST API\"")
        raise typer.Exit(1)

    run_init(requirement, interactive)


@app.command()
def analyze(
    since: str = typer.Option(None, "--since", "-s", help="Analyze changes since commit (default: last commit)"),
    all: bool = typer.Option(False, "--all", "-a", help="Analyze all commits"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis"),
):
    """
    Analyze code changes and track progress.

    Examples:
        deburger analyze                    # Analyze last commit
        deburger analyze --since HEAD~5     # Analyze last 5 commits
        deburger analyze --all              # Analyze all commits
    """
    from deburger.cli.analyze_command import run_analyze

    if all:
        since = "HEAD"
    elif not since:
        since = "HEAD~1"

    run_analyze(since, verbose)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan (default: current directory)"),
    severity: str = typer.Option("all", "--severity", help="Minimum severity: low, medium, high, critical"),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix issues where possible"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show fixes without applying"),
):
    """
    Scan code for security vulnerabilities.

    Examples:
        deburger scan                       # Scan current directory
        deburger scan src/                  # Scan specific directory
        deburger scan --severity high       # Show only high+ severity
        deburger scan --fix                 # Auto-fix issues
        deburger scan --fix --dry-run       # Preview fixes
    """
    from deburger.cli.security_command import run_security_scan

    run_security_scan(path, severity, fix, dry_run)


@app.command()
def watch(
    path: str = typer.Argument(".", help="Path to watch"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Scan interval in seconds"),
):
    """
    Watch directory for changes and scan continuously.

    Examples:
        deburger watch                      # Watch current directory
        deburger watch src/                 # Watch specific directory
        deburger watch --interval 5         # Scan every 5 seconds
    """
    from deburger.cli.watch_command import run_watch

    run_watch(path, interval)


@app.command()
def guide(
    output: str = typer.Option(None, "--output", "-o", help="Save guidance to file"),
):
    """
    Get AI guidance for next development steps.

    Examples:
        deburger guide                      # Show guidance in terminal
        deburger guide -o prompt.txt        # Save to file
    """
    from deburger.cli.guide_command import run_guidance

    run_guidance(output)


@app.command()
def report(
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, html"),
    output: str = typer.Option(None, "--output", "-o", help="Save report to file"),
):
    """
    Generate comprehensive metrics report.

    Examples:
        deburger report                     # Show table report
        deburger report --format json       # JSON output
        deburger report -f html -o report.html
    """
    from deburger.cli.report_command import run_report

    run_report(format, output)


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    clear: bool = typer.Option(False, "--clear", help="Clear all logs"),
):
    """
    View or manage deburger logs.

    Examples:
        deburger logs                       # Show last 50 lines
        deburger logs -n 100                # Show last 100 lines
        deburger logs --follow              # Live tail logs
        deburger logs --clear               # Clear all logs
    """
    from deburger.cli.logs_command import run_logs

    run_logs(lines, follow, clear)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", help="Open config in editor"),
    validate: bool = typer.Option(False, "--validate", help="Validate configuration"),
):
    """
    Manage deburger configuration.

    Examples:
        deburger config --show              # Display current config
        deburger config --edit              # Edit in default editor
        deburger config --validate          # Check config validity
    """
    from deburger.cli.config_command import run_config

    run_config(show, edit, validate)


@app.command()
def version():
    """Show deburger version."""
    from deburger import __version__

    console.print(f"[cyan]deburger[/cyan] version [bold]{__version__}[/bold]")


@app.command()
def selftest():
    """
    Run self-tests to verify installation.

    Tests CLI, git integration, and core functionality.
    """
    from deburger.cli.test_command import run_self_test

    success = run_self_test()
    if not success:
        raise typer.Exit(1)


def main():
    """Main entry point with error handling."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun with --help for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
