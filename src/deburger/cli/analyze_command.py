"""Analyze command with beautiful UI."""

from pathlib import Path

from deburger.orchestrator import DeburgerOrchestrator
from deburger.requirements.tracker import Requirement, SubGoal
from deburger.ui.display import ui


def run_analyze(since: str, config_path: str):
    ui.header("Analyzing code changes...")

    requirement = _load_requirement(config_path)
    guardrails = _load_guardrails(config_path)

    with ui.progress_bar("Running analysis...") as progress:
        task = progress.add_task("Analyzing...", total=100)

        orchestrator = DeburgerOrchestrator(requirement, guardrails)
        progress.update(task, advance=30)

        result = orchestrator.analyze_changes(since)
        progress.update(task, advance=70)

    if result.files_changed == 0:
        ui.warning("No changes found")
        return

    ui.console.print(f"\n{ui.summary_stats(result.files_changed, result.lines_added, result.lines_removed)}\n")

    ui.console.print(ui.requirement_panel(requirement.description, result.requirement_progress))
    ui.console.print()

    ui.console.print(ui.subgoals_table(requirement.sub_goals))
    ui.console.print()

    ui.console.print(ui.security_issues_panel(result.security_issues))
    ui.console.print()

    ui.console.print(ui.metrics_summary(
        quality_score=result.quality_score,
        complexity=10,
        loc=result.lines_added
    ))
    ui.console.print()

    if result.guidance:
        ui.console.print(ui.guidance_panel(result.guidance[:500] + "..."))
        ui.console.print()

    next_goal = [g for g in requirement.sub_goals if g.completion < 0.9]
    if next_goal:
        ui.info(f"Next Focus: {next_goal[0].description}")


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
