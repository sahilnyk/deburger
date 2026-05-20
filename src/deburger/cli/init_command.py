"""Initialize command with interactive prompts."""

from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


def run_init(requirement: str = None, interactive: bool = False):
    """Initialize deburger configuration."""
    from deburger.utils.logger import get_logger
    from deburger.utils.config import DeburgerConfig, SubGoalConfig, LLMConfig, SecurityConfig, MetricsConfig

    logger = get_logger()
    logger.log_command("init", requirement=requirement, interactive=interactive)

    console.print("[bold cyan]🍔 setting things up...[/bold cyan]\n")

    config_path = Path(".deburger.yml")
    if config_path.exists():
        if not Confirm.ask(f"[yellow]{config_path} already exists. Overwrite?[/yellow]"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    if interactive:
        requirement = _interactive_setup()
    elif not requirement:
        console.print("[red]Error: requirement is required[/red]")
        return

    # Create default configuration
    config = DeburgerConfig(
        requirement=requirement,
        sub_goals=[
            SubGoalConfig(
                id="core",
                description="Implement core functionality",
                weight=40,
                keywords=["implement", "add", "create", "function"],
            ),
            SubGoalConfig(
                id="testing",
                description="Add comprehensive tests",
                weight=30,
                keywords=["test", "spec", "assert", "unittest"],
            ),
            SubGoalConfig(
                id="security",
                description="Security hardening",
                weight=20,
                keywords=["security", "auth", "validation", "sanitize"],
            ),
            SubGoalConfig(
                id="docs",
                description="Documentation",
                weight=10,
                keywords=["doc", "readme", "comment", "guide"],
            ),
        ],
        llm=LLMConfig(
            provider="openai",
            model="gpt-4",
            guardrails=[
                "Never disable security features",
                "Always validate user input",
                "Prefer explicit over implicit",
                "No hardcoded credentials",
            ],
        ),
        security=SecurityConfig(
            enabled=True,
            fail_on_high=True,
            fail_on_critical=True,
            ignore_patterns=["tests/", "docs/", "examples/"],
        ),
        metrics=MetricsConfig(
            min_quality_score=70,
            max_complexity=10,
            min_test_coverage=80,
        ),
    )

    # Save configuration
    config.save(str(config_path))
    console.print(f"[green]done:[/green] created {config_path}")

    # Update .gitignore
    _update_gitignore()

    # Show next steps
    console.print("\n[bold cyan]what's next:[/bold cyan]")
    console.print("  1. set your api key: [cyan]export OPENAI_API_KEY=your-key[/cyan]")
    console.print("  2. code something with AI")
    console.print("  3. commit: [cyan]git commit -m 'your changes'[/cyan]")
    console.print("  4. run: [cyan]deburger analyze[/cyan]")
    console.print()
    console.print("[dim]edit .deburger.yml to tweak goals and settings[/dim]")

    logger.info("Initialized deburger", requirement=requirement)


def _interactive_setup() -> str:
    """Interactive configuration wizard."""
    console.print("[bold]quick setup[/bold]\n")

    requirement = Prompt.ask("what's your main goal for this project?")

    console.print(f"\n[green]got it:[/green] {requirement}")
    console.print("\n[dim]you can tweak sub-goals by editing .deburger.yml[/dim]\n")

    return requirement


def _update_gitignore():
    """Add deburger files to .gitignore."""
    gitignore_path = Path(".gitignore")

    entries_to_add = [
        ".deburger.cache",
        ".deburger/logs/",
    ]

    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()

        new_entries = []
        for entry in entries_to_add:
            if entry not in gitignore_content:
                new_entries.append(entry)

        if new_entries:
            with gitignore_path.open("a") as f:
                f.write("\n# deburger\n")
                for entry in new_entries:
                    f.write(f"{entry}\n")
            console.print(f"[green]done:[/green] updated .gitignore")
    else:
        with gitignore_path.open("w") as f:
            f.write("# deburger\n")
            for entry in entries_to_add:
                f.write(f"{entry}\n")
        console.print(f"[green]done:[/green] created .gitignore")
