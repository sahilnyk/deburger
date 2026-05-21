"""Security scan command with multi-language support."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.text import Text
from rich import box
import time

console = Console()


def run_security_scan(path: str, severity: str = "all", fix: bool = False, dry_run: bool = False):
    """Run comprehensive security scan across multiple languages."""
    from deburger.utils.logger import get_logger
    from deburger.utils.config import load_config
    from deburger.security.multi_language_scanner import (
        MultiLanguageScanner,
        Severity as SevEnum,
    )
    from deburger.fixer.auto_fixer import AutoFixer

    logger = get_logger()
    logger.log_command("scan", path=path, severity=severity, fix=fix)

    # Cool scanning animation
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("🍔"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        scan_task = progress.add_task("scanning for security issues", total=100)

        # Simulate scanning progress
        for i in range(100):
            progress.update(scan_task, advance=1)
            time.sleep(0.01)

    console.print()

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

    # Display cool summary with gradient border
    summary_text = Text()
    summary_text.append("Scanned: ", style="bold cyan")
    summary_text.append(f"{path}\n")
    summary_text.append("Issues Found: ", style="bold cyan")

    if total_issues == 0:
        summary_text.append(f"{total_issues}", style="bold green")
    elif total_issues < 5:
        summary_text.append(f"{total_issues}", style="bold yellow")
    else:
        summary_text.append(f"{total_issues}", style="bold red")

    summary_text.append("\nFiles Affected: ", style="bold cyan")
    summary_text.append(f"{files_affected}\n")
    summary_text.append("Languages: ", style="bold cyan")
    summary_text.append(', '.join(sorted(languages)) if languages else 'None', style="magenta")

    console.print(Panel(
        summary_text,
        title="[bold]🍔 Scan Results[/bold]",
        border_style="cyan bold",
        box=box.DOUBLE
    ))
    console.print()

    if not vulnerabilities:
        # Victory animation
        console.print()
        console.print(Panel(
            "[bold green]✓ CLEAN CODE ✓[/bold green]\n\n"
            "[green]no security issues detected[/green]\n"
            "[dim]your code is looking good[/dim]",
            title="[bold green]Success[/bold green]",
            border_style="green bold",
            box=box.DOUBLE
        ))
        logger.info("Security scan completed", issues=0, path=path)
        return

    # Display issues by severity with cool styling
    for sev_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        issues = grouped[sev_level]
        if not issues:
            continue

        color = _get_severity_color(sev_level)

        console.print(f"\n[bold {color}]{sev_level}[/bold {color}] [dim]({len(issues)} issue{'s' if len(issues) > 1 else ''})[/dim]")
        console.print("─" * 90)

        table = Table(
            show_header=True,
            header_style=f"bold {color}",
            box=box.SIMPLE,
            padding=(0, 2),
            border_style=color
        )
        table.add_column("File", style="cyan", no_wrap=False, max_width=35)
        table.add_column("Line", justify="center", style="dim", width=6)
        table.add_column("Issue", no_wrap=False, max_width=45)
        table.add_column("Lang", style="magenta", width=8)

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

    # Show detailed examples with cool panels
    console.print()
    critical_and_high = grouped["CRITICAL"] + grouped["HIGH"]

    if critical_and_high:
        console.print(Panel(
            "[bold red]Top Issues Requiring Attention[/bold red]",
            border_style="red",
            box=box.DOUBLE
        ))

        for i, vuln in enumerate(critical_and_high[:3], 1):
            issue_panel = Text()
            issue_panel.append(f"{i}. ", style="bold yellow")
            issue_panel.append(f"{vuln.description}\n", style="bold white")
            issue_panel.append(f"   Location: ", style="dim")
            issue_panel.append(f"{vuln.file_path}:{vuln.line}\n", style="cyan")
            issue_panel.append(f"   Code: ", style="dim")
            issue_panel.append(f"{vuln.code_snippet}\n", style="dim")

            if vuln.fix_suggestion:
                issue_panel.append(f"   Fix: ", style="green bold")
                issue_panel.append(f"{vuln.fix_suggestion}\n", style="green")

            if vuln.cwe_id:
                issue_panel.append(f"   CWE: ", style="dim")
                issue_panel.append(f"{vuln.cwe_id}", style="blue dim")

            console.print(Panel(issue_panel, border_style="yellow", box=box.ROUNDED))
            console.print()

    # Auto-fix (if requested and supported)
    if fix:
        console.print()
        with Progress(
            SpinnerColumn(spinner_name="arc"),
            TextColumn("🍔"),
            TextColumn("[bold magenta]{task.description}"),
            console=console,
        ) as progress:
            fix_task = progress.add_task("generating fixes...", total=None)
            time.sleep(0.5)  # Dramatic pause

            fixer = AutoFixer()
            fixes = []

            for vuln in vulnerabilities:
                if fixer.can_fix(vuln):
                    fix_obj = fixer.generate_fix(vuln)
                    if fix_obj:
                        fixes.append(fix_obj)

        console.print()

        if not fixes:
            console.print(Panel(
                "[yellow]no auto-fixable issues found[/yellow]\n"
                "[dim]these issues need manual review[/dim]",
                title="[bold yellow]Auto-Fix Status[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED
            ))
        else:
            console.print(Panel(
                f"[bold green]✓ Generated {len(fixes)} fix{'es' if len(fixes) > 1 else ''}[/bold green]",
                border_style="green",
                box=box.DOUBLE
            ))
            console.print()

            # Show fixes with cool diff styling
            for i, fix_obj in enumerate(fixes[:5], 1):
                fix_panel = Text()
                fix_panel.append(f"Fix #{i}: ", style="bold cyan")
                fix_panel.append(f"{fix_obj.description}\n\n", style="white")
                fix_panel.append(f"Location: ", style="dim")
                fix_panel.append(f"{Path(fix_obj.file_path).name}:{fix_obj.original_line}\n\n", style="cyan")
                fix_panel.append(f"  - ", style="red bold")
                fix_panel.append(f"{fix_obj.original_code}\n", style="red")
                fix_panel.append(f"  + ", style="green bold")
                fix_panel.append(f"{fix_obj.fixed_code}", style="green")

                console.print(Panel(
                    fix_panel,
                    border_style="magenta",
                    box=box.ROUNDED,
                    title=f"[bold magenta]Fix {i}/{min(len(fixes), 5)}[/bold magenta]"
                ))
                console.print()

            if len(fixes) > 5:
                console.print(f"[dim cyan]... and {len(fixes) - 5} more fixes available[/dim cyan]\n")

            if dry_run:
                console.print(Panel(
                    "[bold yellow]DRY RUN MODE[/bold yellow]\n\n"
                    "[yellow]no changes applied[/yellow]\n"
                    "[dim]remove --dry-run to apply fixes[/dim]",
                    border_style="yellow bold",
                    box=box.DOUBLE
                ))
            else:
                # Apply fixes with progress
                with Progress(
                    SpinnerColumn(spinner_name="dots"),
                    TextColumn("🍔"),
                    TextColumn("[bold green]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    apply_task = progress.add_task("applying fixes", total=len(fixes))
                    applied = fixer.apply_fixes(fixes, dry_run=False)
                    progress.update(apply_task, advance=len(fixes))

                console.print()
                console.print(Panel(
                    f"[bold green]✓ FIXED![/bold green]\n\n"
                    f"[green]applied {applied} fix{'es' if applied > 1 else ''}[/green]\n"
                    f"[dim]review changes with: git diff[/dim]\n"
                    f"[dim]commit when ready: git commit -am 'fixed security issues'[/dim]",
                    title="[bold green]Success[/bold green]",
                    border_style="green bold",
                    box=box.DOUBLE
                ))

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

    # Final verdict with cool styling
    console.print()
    if critical_count > 0:
        console.print(Panel(
            f"[bold red]CRITICAL: {critical_count} issue{'s' if critical_count > 1 else ''} found[/bold red]\n\n"
            f"[red]these need immediate attention[/red]\n"
            f"[dim]run with --fix to auto-fix[/dim]",
            title="[bold red]Action Required[/bold red]",
            border_style="red bold",
            box=box.DOUBLE
        ))
    elif high_count > 0:
        console.print(Panel(
            f"[bold yellow]HIGH: {high_count} issue{'s' if high_count > 1 else ''} found[/bold yellow]\n\n"
            f"[yellow]should probably fix these soon[/yellow]\n"
            f"[dim]run with --fix to auto-fix[/dim]",
            title="[bold yellow]Needs Attention[/bold yellow]",
            border_style="yellow bold",
            box=box.ROUNDED
        ))
    else:
        console.print(Panel(
            f"[bold green]✓ Looking good![/bold green]\n\n"
            f"[green]{total_issues} minor issue{'s' if total_issues > 1 else ''} found[/green]\n"
            f"[dim]nothing critical[/dim]",
            title="[bold green]Nice Work[/bold green]",
            border_style="green",
            box=box.ROUNDED
        ))


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
