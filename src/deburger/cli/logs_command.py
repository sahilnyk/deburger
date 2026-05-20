"""Logs command to view and manage logs."""

import time
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

console = Console()


def run_logs(lines: int, follow: bool, clear: bool):
    """View or manage deburger logs."""
    from deburger.utils.logger import get_logger

    logger = get_logger()

    if clear:
        logger.clear_logs()
        console.print("[green]✓[/green] Logs cleared")
        return

    log_file = Path.home() / ".deburger" / "logs" / "deburger.log"

    if not log_file.exists():
        console.print("[yellow]No logs found[/yellow]")
        console.print("Logs will be created when you run deburger commands")
        return

    if follow:
        console.print("[cyan]Following logs... (Press Ctrl+C to stop)[/cyan]\n")
        _follow_logs(log_file)
    else:
        _show_logs(log_file, lines)


def _show_logs(log_file: Path, lines: int):
    """Show last N lines of logs."""
    with open(log_file, "r") as f:
        all_lines = f.readlines()
        recent_lines = all_lines[-lines:]

    if not recent_lines:
        console.print("[yellow]No logs found[/yellow]")
        return

    console.print(f"[cyan]Last {len(recent_lines)} log entries:[/cyan]\n")

    for line in recent_lines:
        line = line.strip()
        if "ERROR" in line or "CRITICAL" in line:
            console.print(f"[red]{line}[/red]")
        elif "WARNING" in line:
            console.print(f"[yellow]{line}[/yellow]")
        elif "INFO" in line:
            console.print(f"[blue]{line}[/blue]")
        else:
            console.print(line)


def _follow_logs(log_file: Path):
    """Follow logs in real-time (tail -f style)."""
    with open(log_file, "r") as f:
        # Go to end of file
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if line:
                    line = line.strip()
                    if "ERROR" in line or "CRITICAL" in line:
                        console.print(f"[red]{line}[/red]")
                    elif "WARNING" in line:
                        console.print(f"[yellow]{line}[/yellow]")
                    elif "INFO" in line:
                        console.print(f"[blue]{line}[/blue]")
                    else:
                        console.print(line)
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following logs[/yellow]")
