"""Report generation command."""

from rich.console import Console

console = Console()


def run_report(format: str):
    console.print(f"[cyan]generating {format} report...[/cyan]\n")

    console.print("[yellow]Report generation not yet implemented[/yellow]")
