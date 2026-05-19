"""Analyze command implementation."""

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from deburger.analyzer.diff_analyzer import DiffAnalyzer
from deburger.security.scanner import SecurityScanner
from deburger.metrics.calculator import MetricsCalculator
from deburger.requirements.tracker import RequirementTracker, Requirement, SubGoal

console = Console()


def run_analyze(since: str, config_path: str):
    console.print("[cyan]🍔 Analyzing code changes...[/cyan]\n")

    analyzer = DiffAnalyzer()
    changes = analyzer.get_changes(since)

    if not changes:
        console.print("[yellow]No changes found[/yellow]")
        return

    console.print(f"[green]Found {len(changes)} changed files[/green]\n")

    requirement = _load_requirement(config_path)
    tracker = RequirementTracker(requirement)
    progress = tracker.calculate_progress(changes)

    console.print(Panel(
        f"[bold]Requirement:[/bold] {requirement.description}\n"
        f"[bold]Progress:[/bold] {progress:.0%}",
        title="📊 Requirement Progress",
        border_style="green",
    ))

    _show_subgoals(requirement)

    scanner = SecurityScanner()
    all_vulns = []
    for change in changes:
        try:
            content = analyzer.get_file_content(change.file_path)
            vulns = scanner.scan_file(change.file_path, content)
            all_vulns.extend(vulns)
        except Exception:
            pass

    if all_vulns:
        _show_security_issues(all_vulns)
    else:
        console.print("\n[green]✓ No security issues found[/green]")

    metrics_calc = MetricsCalculator()
    total_metrics = []
    for change in changes:
        try:
            content = analyzer.get_file_content(change.file_path)
            metrics = metrics_calc.calculate(change.file_path, content)
            total_metrics.append(metrics)
        except Exception:
            pass

    if total_metrics:
        avg_score = sum(m.overall_score for m in total_metrics) / len(total_metrics)
        console.print(f"\n[cyan]Code Quality Score:[/cyan] {avg_score:.0f}/100")

    next_focus = tracker.get_next_focus()
    if next_focus:
        console.print(
            f"\n[yellow]→ Next Focus:[/yellow] {next_focus.description} ({next_focus.completion:.0%} complete)"
        )


def _load_requirement(config_path: str) -> Requirement:
    return Requirement(
        description="Build quality code monitoring system",
        sub_goals=[
            SubGoal(id="analyzer", description="Implement code change analysis", weight=30),
            SubGoal(id="security", description="Add security scanning", weight=25),
            SubGoal(id="metrics", description="Calculate quality metrics", weight=20),
            SubGoal(id="requirements", description="Track requirement progress", weight=25),
        ],
    )


def _show_subgoals(requirement: Requirement):
    table = Table(title="Sub-Goals Progress")
    table.add_column("Goal", style="cyan")
    table.add_column("Progress", style="green")
    table.add_column("Status", style="yellow")

    for goal in requirement.sub_goals:
        status = "✓" if goal.completion >= 0.9 else "↑" if goal.completion >= 0.5 else "⚠"
        table.add_row(
            goal.description,
            f"{goal.completion:.0%}",
            status,
        )

    console.print(table)


def _show_security_issues(vulns: list):
    console.print(f"\n[red]Security Issues ({len(vulns)}):[/red]")
    for vuln in vulns[:10]:
        severity_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}[vuln.severity.value]
        console.print(f"[{severity_color}]├─ {vuln.severity.value}:[/{severity_color}] {vuln.description} (line {vuln.line})")
        if vuln.fix_suggestion:
            console.print(f"   [dim]Fix: {vuln.fix_suggestion}[/dim]")
