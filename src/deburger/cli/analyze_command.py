"""Analyze command with beautiful UI."""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_analyze(since: str, verbose: bool = False):
    """Analyze code changes and track progress."""
    from deburger.utils.logger import get_logger
    from deburger.utils.config import load_config
    from deburger.orchestrator import DeburgerOrchestrator
    from deburger.requirements.tracker import Requirement, SubGoal
    from deburger.ui.display import ui

    logger = get_logger()
    logger.log_command("analyze", since=since, verbose=verbose)

    console.print("🍔 [bold cyan]analyzing your code...[/bold cyan]\n")

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [cyan]deburger init[/cyan] to create configuration")
        return

    # Convert config to Requirement object
    requirement = Requirement(
        description=config.requirement,
        sub_goals=[
            SubGoal(
                id=sg.id,
                description=sg.description,
                weight=sg.weight / 100.0,  # Convert to 0-1 scale
                keywords=sg.keywords,
            )
            for sg in config.sub_goals
        ],
    )

    # Run analysis with progress indicator
    with Progress(
        SpinnerColumn(spinner_name="bouncingBall"),
        TextColumn("🍔"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("analyzing code changes...", total=None)

        try:
            orchestrator = DeburgerOrchestrator(requirement, config.llm.guardrails)
            result = orchestrator.analyze_changes(since)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            console.print(f"\n[red]Error:[/red] {e}")
            return

    if result.files_changed == 0:
        console.print("[yellow]heads up:[/yellow] no changes found since {since}")
        console.print("\n[dim]make some changes and commit, then run this again[/dim]")
        return

    # Display results
    console.print(
        f"\n[bold]Files:[/bold] {result.files_changed} | "
        f"[green]+{result.lines_added}[/green] [red]-{result.lines_removed}[/red]\n"
    )

    ui.console.print(ui.requirement_panel(requirement.description, result.requirement_progress))
    ui.console.print()

    ui.console.print(ui.subgoals_table(requirement.sub_goals))
    ui.console.print()

    ui.console.print(ui.security_issues_panel(result.security_issues))
    ui.console.print()

    ui.console.print(
        ui.metrics_summary(
            quality_score=result.quality_score, complexity=10, loc=result.lines_added
        )
    )
    ui.console.print()

    if result.guidance and verbose:
        ui.console.print(ui.guidance_panel(result.guidance[:500] + "..."))
        ui.console.print()

    # Show next focus
    next_goal = [g for g in requirement.sub_goals if g.completion < 0.9]
    if next_goal:
        console.print(
            f"[bold cyan]up next:[/bold cyan] {next_goal[0].description}"
        )

    # Log results
    logger.log_analysis(
        files=result.files_changed,
        lines_added=result.lines_added,
        lines_removed=result.lines_removed,
        progress=result.requirement_progress,
        security_issues=len(result.security_issues),
    )
