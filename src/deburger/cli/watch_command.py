"""Watch mode for continuous monitoring."""

from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

console = Console()


def run_watch(path: str = ".", interval: float = 2.0):
    """Watch directory for changes and scan continuously."""
    from deburger.watcher.file_watcher import FileWatcher
    from deburger.security.multi_language_scanner import MultiLanguageScanner

    console.print("🍔 [bold cyan]starting watch mode...[/bold cyan]\n")
    console.print(f"[dim]watching: {Path(path).absolute()}[/dim]")
    console.print(f"[dim]scan interval: {interval}s[/dim]")
    console.print("[dim]press Ctrl+C to stop[/dim]\n")

    scanner = MultiLanguageScanner()
    scan_count = 0
    last_scan_time = None
    last_issues_count = 0

    def on_change(changed_path: str):
        """Callback when files change."""
        nonlocal scan_count, last_scan_time, last_issues_count

        scan_count += 1
        last_scan_time = datetime.now().strftime("%H:%M:%S")

        # Scan the directory
        vulnerabilities = scanner.scan_directory(
            changed_path,
            recursive=True,
            ignore_patterns=[".git", "__pycache__", "node_modules"],
        )

        last_issues_count = len(vulnerabilities)

        # Display update
        console.clear()
        console.print("🍔 [bold cyan]watch mode active[/bold cyan]\n")

        # Stats table
        stats = Table(show_header=False, box=None, padding=(0, 2))
        stats.add_column("Label", style="cyan")
        stats.add_column("Value", style="green")
        stats.add_row("Path", str(Path(path).absolute()))
        stats.add_row("Scans", str(scan_count))
        stats.add_row("Last scan", last_scan_time)
        stats.add_row("Issues", str(last_issues_count))

        console.print(Panel(stats, title="Status", border_style="cyan"))
        console.print()

        # Show recent issues
        if vulnerabilities:
            issues_table = Table(title="Recent Issues", show_header=True)
            issues_table.add_column("File", style="cyan", no_wrap=False, max_width=30)
            issues_table.add_column("Line", justify="right", style="dim")
            issues_table.add_column("Severity", style="red")
            issues_table.add_column("Type", style="yellow")

            for vuln in vulnerabilities[:5]:
                file_name = Path(vuln.file_path).name
                severity_color = "red" if vuln.severity.value in ["CRITICAL", "HIGH"] else "yellow"
                issues_table.add_row(
                    file_name,
                    str(vuln.line),
                    f"[{severity_color}]{vuln.severity.value}[/{severity_color}]",
                    vuln.type,
                )

            console.print(issues_table)
            console.print()

            if len(vulnerabilities) > 5:
                console.print(f"[dim]... and {len(vulnerabilities) - 5} more issues[/dim]\n")

            console.print("[yellow]run 'deburger scan --fix' to auto-fix[/yellow]")
        else:
            console.print("[green]✓ no issues found[/green]")

        console.print("\n[dim]press Ctrl+C to stop[/dim]")

    # Create and start watcher
    watcher = FileWatcher(
        watch_path=path, callback=on_change, interval=interval
    )

    try:
        console.print("[cyan]watching for changes...[/cyan]\n")
        watcher.watch()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]stopping watch mode...[/yellow]")
        watcher.stop()
        console.print(f"[green]✓ completed {scan_count} scans[/green]")
