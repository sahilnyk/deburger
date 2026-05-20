"""Configuration command."""

import subprocess
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

console = Console()


def run_config(show: bool = False, edit: bool = False, validate: bool = False):
    """Manage deburger configuration."""
    from deburger.utils.logger import get_logger
    from deburger.utils.config import load_config

    logger = get_logger()

    config_path = Path(".deburger.yml")

    if not config_path.exists():
        console.print("[red]Error:[/red] No configuration found")
        console.print("Run [cyan]deburger init[/cyan] to create configuration")
        return

    if validate:
        _validate_config(config_path)
    elif edit:
        _edit_config(config_path)
    else:
        # Default: show config
        _show_config(config_path)

    logger.log_command("config", show=show, edit=edit, validate=validate)


def _show_config(config_path: Path):
    """Display current configuration."""
    console.print("[bold cyan]your config:[/bold cyan]\n")

    content = config_path.read_text()
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)

    console.print(f"\n[dim]file: {config_path.absolute()}[/dim]")


def _edit_config(config_path: Path):
    """Open config in default editor."""
    import os

    editor = os.environ.get("EDITOR", "nano")

    try:
        subprocess.run([editor, str(config_path)])
        console.print("[green]done:[/green] config updated")
    except Exception as e:
        console.print(f"[red]couldn't open editor:[/red] {e}")
        console.print(f"edit manually: {config_path.absolute()}")


def _validate_config(config_path: Path):
    """Validate configuration file."""
    from deburger.utils.config import load_config

    console.print("[bold cyan]checking your config...[/bold cyan]\n")

    try:
        config = load_config(str(config_path))
        errors = config.validate()

        if errors:
            console.print("[red]found some issues:[/red]\n")
            for error in errors:
                console.print(f"  - {error}")
        else:
            console.print("[green]looks good![/green]\n")
            console.print(f"[bold]goal:[/bold] {config.requirement}")
            console.print(f"[bold]sub-goals:[/bold] {len(config.sub_goals)}")
            console.print(f"[bold]llm:[/bold] {config.llm.provider}")
            console.print(f"[bold]security:[/bold] {'on' if config.security.enabled else 'off'}")

    except Exception as e:
        console.print(f"[red]config is broken:[/red] {e}")
