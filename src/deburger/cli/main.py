"""Main CLI entry point for deburger."""

import typer
from rich.console import Console

app = typer.Typer(
    name="deburger",
    help="🍔 AI Code Quality Guardian - Monitor AI-generated code",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(requirement: str = typer.Option(..., "--requirement", "-r", help="Main requirement")):
    """Initialize deburger configuration."""
    from deburger.cli.init_command import run_init

    run_init(requirement)


@app.command()
def analyze(
    since: str = typer.Option("HEAD~1", "--since", help="Analyze changes since commit"),
    config_path: str = typer.Option(".deburger.yml", "--config", help="Config file path"),
):
    """Analyze code changes."""
    from deburger.cli.analyze_command import run_analyze

    run_analyze(since, config_path)


@app.command()
def security(
    path: str = typer.Option(".", "--path", help="Path to scan"),
):
    """Run security vulnerability scan."""
    from deburger.cli.security_command import run_security_scan

    run_security_scan(path)


@app.command()
def report(
    format: str = typer.Option("text", "--format", help="Output format (text/html/json)"),
):
    """Generate metrics report."""
    from deburger.cli.report_command import run_report

    run_report(format)


@app.command()
def guide():
    """Get AI guidance for next steps."""
    from deburger.cli.guide_command import run_guidance

    run_guidance()


@app.command()
def config():
    """Configure deburger settings."""
    from deburger.cli.config_command import run_config

    run_config()


@app.command()
def version():
    """Show deburger version."""
    console.print("🍔 deburger v0.2.0")


if __name__ == "__main__":
    app()
