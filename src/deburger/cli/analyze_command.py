"""Analyze command with beautiful UI."""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from rich import box
import time

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

    console.print()
    console.print(Panel(
        "[bold cyan]🍔 Code Analysis[/bold cyan]\n"
        "[dim]scanning changes, checking quality, tracking progress[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))
    console.print()

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

    # Run analysis with cool progress animation
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("🍔"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("analyzing code changes", total=100)

        # Simulate analysis stages
        progress.update(task, description="scanning files", completed=20)
        time.sleep(0.2)
        progress.update(task, description="checking security", completed=50)
        time.sleep(0.2)
        progress.update(task, description="calculating metrics", completed=80)
        time.sleep(0.2)

        try:
            orchestrator = DeburgerOrchestrator(requirement, config.llm.guardrails)
            result = orchestrator.analyze_changes(since)
            progress.update(task, description="finalizing", completed=100)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            console.print()
            console.print(Panel(
                f"[red]Analysis failed:[/red]\n{e}",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.ROUNDED
            ))
            return

    if result.files_changed == 0:
        console.print()
        console.print(Panel(
            "[yellow]heads up - no changes detected[/yellow]\n\n"
            f"[dim]no commits found since {since}[/dim]\n"
            "[dim]make some changes, commit, then run again[/dim]",
            title="[bold yellow]No Changes[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        ))
        return

    # Display cool change summary
    console.print()
    change_text = Text()
    change_text.append("Files Changed: ", style="bold cyan")
    change_text.append(f"{result.files_changed}  ", style="white")
    change_text.append("│  ", style="dim")
    change_text.append("+", style="green bold")
    change_text.append(f"{result.lines_added} ", style="green")
    change_text.append("│  ", style="dim")
    change_text.append("-", style="red bold")
    change_text.append(f"{result.lines_removed}", style="red")

    console.print(Panel(change_text, border_style="cyan", box=box.SIMPLE))
    console.print()

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
