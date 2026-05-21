"""Security scan command with multi-language support."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def run_security_scan(path: str, severity: str = "all", fix: bool = False):
    """Run comprehensive security scan across multiple languages."""
    from deburger.utils.logger import get_logger
    from deburger.utils.config import load_config
    from deburger.security.multi_language_scanner import (
        MultiLanguageScanner,
        Severity as SevEnum,
    )

    logger = get_logger()
    logger.log_command("scan", path=path, severity=severity, fix=fix)

    console.print("🍔 [bold cyan]scanning for security issues...[/bold cyan]\n")

    # Load config for ignore patterns
    try:
        config = load_config()
        ignore_patterns = config.security.ignore_patterns
    except FileNotFoundError:
        ignore_patterns = ["tests/", "docs/", "examples/", "__pycache__/", ".git/"]

    # Create scanner
    scanner = MultiLanguageScanner()

    # Determine minimum severity
    severity_map = {
        "all": SevEnum.INFO,
        "low": SevEnum.LOW,
        "medium": SevEnum.MEDIUM,
        "high": SevEnum.HIGH,
        "critical": SevEnum.CRITICAL,
    }
    min_severity = severity_map.get(severity.lower(), SevEnum.INFO)

    # Scan directory or file
    scan_path = Path(path)
    if scan_path.is_file():
        vulnerabilities = scanner.scan_file(str(scan_path))
    else:
        vulnerabilities = scanner.scan_directory(
            str(scan_path), recursive=True, ignore_patterns=ignore_patterns
        )

    # Filter by severity
    vulnerabilities = scanner.filter_by_severity(vulnerabilities, min_severity)

    # Group by severity
    grouped = {
        "CRITICAL": [v for v in vulnerabilities if v.severity == SevEnum.CRITICAL],
        "HIGH": [v for v in vulnerabilities if v.severity == SevEnum.HIGH],
        "MEDIUM": [v for v in vulnerabilities if v.severity == SevEnum.MEDIUM],
        "LOW": [v for v in vulnerabilities if v.severity == SevEnum.LOW],
        "INFO": [v for v in vulnerabilities if v.severity == SevEnum.INFO],
    }

    # Calculate statistics
    total_issues = len(vulnerabilities)
    files_affected = len(set(v.file_path for v in vulnerabilities))
    languages = set(v.language for v in vulnerabilities)

    # Display summary
    console.print(Panel(
        f"[bold]Scanned:[/bold] {path}\n"
        f"[bold]Issues Found:[/bold] {total_issues}\n"
        f"[bold]Files Affected:[/bold] {files_affected}\n"
        f"[bold]Languages:[/bold] {', '.join(sorted(languages)) if languages else 'None'}",
        title="Scan Summary",
        border_style="cyan"
    ))
    console.print()

    if not vulnerabilities:
        console.print("[green]nice! no security issues found[/green]")
        logger.info("Security scan completed", issues=0, path=path)
        return

    # Display issues by severity
    for sev_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        issues = grouped[sev_level]
        if not issues:
            continue

        color = _get_severity_color(sev_level)
        console.print(f"\n[bold {color}]{sev_level} ({len(issues)})[/bold {color}]")
        console.print("─" * 80)

        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("File", style="cyan", no_wrap=False, max_width=40)
        table.add_column("Line", justify="right", style="dim")
        table.add_column("Issue", no_wrap=False)
        table.add_column("Language", style="magenta")

        for vuln in issues[:10]:  # Show max 10 per severity
            file_display = Path(vuln.file_path).name
            table.add_row(
                file_display,
                str(vuln.line),
                f"{vuln.description}",
                vuln.language,
            )

            # Log each issue
            logger.log_security_issue(
                issue_type=vuln.type,
                severity=sev_level,
                file_path=vuln.file_path,
                line=vuln.line,
            )

        console.print(table)

        if len(issues) > 10:
            console.print(f"[dim]... and {len(issues) - 10} more[/dim]")

    # Show detailed examples
    console.print("\n[bold]Example Issues:[/bold]")
    critical_and_high = grouped["CRITICAL"] + grouped["HIGH"]

    for i, vuln in enumerate(critical_and_high[:3], 1):
        console.print(f"\n[bold]{i}. {vuln.description}[/bold]")
        console.print(f"   [cyan]{vuln.file_path}:{vuln.line}[/cyan]")
        console.print(f"   [dim]{vuln.code_snippet}[/dim]")
        if vuln.fix_suggestion:
            console.print(f"   [green]Fix:[/green] {vuln.fix_suggestion}")
        if vuln.cwe_id:
            console.print(f"   [dim]CWE: {vuln.cwe_id}[/dim]")

    # Auto-fix (if requested and supported)
    if fix:
        console.print("\n[yellow]heads up:[/yellow] auto-fix isn't ready yet")

    # Exit code based on severity
    critical_count = len(grouped["CRITICAL"])
    high_count = len(grouped["HIGH"])

    logger.info(
        "Security scan completed",
        total_issues=total_issues,
        critical=critical_count,
        high=high_count,
        path=path,
    )

    if critical_count > 0:
        console.print(
            f"\n[bold red]yikes! {critical_count} critical issue(s) - fix these asap[/bold red]"
        )
    elif high_count > 0:
        console.print(f"\n[bold yellow]found {high_count} high severity issue(s) - should probably fix[/bold yellow]")


def _get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "CRITICAL": "red",
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "blue",
        "INFO": "cyan",
    }
    return colors.get(severity, "white")
