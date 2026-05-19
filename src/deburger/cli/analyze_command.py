"""Analyze command implementation."""

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from deburger.orchestrator import DeburgerOrchestrator
from deburger.requirements.tracker import Requirement, SubGoal

console = Console()


def run_analyze(since: str, config_path: str):
    console.print("[cyan]🍔 Analyzing code changes...[/cyan]\n")

    requirement = _load_requirement(config_path)
    guardrails = _load_guardrails(config_path)

    orchestrator = DeburgerOrchestrator(requirement, guardrails)
    result = orchestrator.analyze_changes(since)

    if result.files_changed == 0:
        console.print("[yellow]No changes found[/yellow]")
        return

    console.print(f"[green]Analyzed {result.files_changed} files (+{result.lines_added} -{result.lines_removed} lines)[/green]\n")

    console.print(Panel(
        f"[bold]Requirement:[/bold] {requirement.description}\n"
        f"[bold]Progress:[/bold] {result.requirement_progress:.0%}",
        title="📊 Requirement Progress",
        border_style="green",
    ))

    _show_subgoals(requirement)

    if result.security_issues:
        _show_security_issues(result.security_issues)
    else:
        console.print("\n[green]✓ No security issues found[/green]")

    console.print(f"\n[cyan]Code Quality Score:[/cyan] {result.quality_score:.0f}/100")

    if result.guidance:
        console.print("\n[bold cyan]AI Guidance:[/bold cyan]")
        console.print(Panel(Markdown(result.guidance), border_style="cyan"))
    else:
        next_goal = [g for g in requirement.sub_goals if g.completion < 0.9]
        if next_goal:
            console.print(
                f"\n[yellow]→ Next Focus:[/yellow] {next_goal[0].description}"
            )


def _load_requirement(config_path: str) -> Requirement:
    return Requirement(
        description="Build AI code quality monitoring system",
        sub_goals=[
            SubGoal(id="analyzer", description="Code change analysis", weight=25),
            SubGoal(id="security", description="Security vulnerability scanning", weight=25),
            SubGoal(id="metrics", description="Quality metrics calculation", weight=20),
            SubGoal(id="requirements", description="Requirement progress tracking", weight=15),
            SubGoal(id="guidance", description="AI steering and guidance", weight=15),
        ],
    )


def _load_guardrails(config_path: str) -> list[str]:
    return [
        "Never disable security features",
        "Always validate user input",
        "No hardcoded credentials",
        "Prefer explicit over implicit",
    ]


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
