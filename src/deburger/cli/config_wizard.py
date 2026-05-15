"""Interactive configuration wizard for deburger."""

from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def run_config_wizard():
    """Run the interactive configuration wizard."""
    console.clear()

    # Welcome banner
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🍔 deburger setup wizard[/bold cyan]\n\n"
        "Let's get you set up in like 2 minutes",
        border_style="cyan"
    ))
    console.print()

    config = {}

    # Step 1: API Keys
    console.print("[bold yellow]Step 1:[/bold yellow] API Configuration")
    console.print("You need at least one AI provider. We support:")
    console.print("  • OpenAI (GPT-4) - best quality, costs money")
    console.print("  • Anthropic (Claude) - also great, also costs money")
    console.print("  • Ollama (local) - free but slower\n")

    # OpenAI
    use_openai = Confirm.ask("Do you have an OpenAI API key?", default=True)
    if use_openai:
        openai_key = Prompt.ask("  Paste your OpenAI API key", password=True)
        if not config.get("api"):
            config["api"] = {"providers": []}
        config["api"]["providers"].append({
            "name": "openai",
            "api_key": f"${{{openai_key}}}",
            "model": "gpt-4",
            "enabled": True
        })

    console.print()

    # Anthropic
    use_anthropic = Confirm.ask("Do you have an Anthropic API key?", default=False)
    if use_anthropic:
        anthropic_key = Prompt.ask("  Paste your Anthropic API key", password=True)
        if not config.get("api"):
            config["api"] = {"providers": []}
        config["api"]["providers"].append({
            "name": "anthropic",
            "api_key": f"${{{anthropic_key}}}",
            "model": "claude-3-5-sonnet-20241022",
            "enabled": True
        })

    console.print()

    # Ollama
    use_ollama = Confirm.ask("Want to use Ollama (local, free)?", default=False)
    if use_ollama:
        ollama_url = Prompt.ask("  Ollama base URL", default="http://localhost:11434")
        if not config.get("api"):
            config["api"] = {"providers": []}
        config["api"]["providers"].append({
            "name": "ollama",
            "base_url": ollama_url,
            "model": "llama3",
            "enabled": True
        })

    console.print()

    # Step 2: Budget
    console.print("[bold yellow]Step 2:[/bold yellow] Budget & Cost Control")

    set_budget = Confirm.ask("Want to set a spending limit?", default=True)
    if set_budget:
        budget = Prompt.ask("  Max cost per run (USD)", default="5.0")
        if not config.get("api"):
            config["api"] = {}
        config["api"]["budget"] = {
            "max_cost_per_run": float(budget),
            "alert_threshold": float(budget) * 0.8
        }

    console.print()

    # Step 3: Testing
    console.print("[bold yellow]Step 3:[/bold yellow] Test Configuration")

    test_runner = Prompt.ask(
        "  Test runner",
        choices=["pytest", "unittest"],
        default="pytest"
    )
    test_path = Prompt.ask("  Test directory", default="tests/")

    config["testing"] = {
        "runner": test_runner,
        "test_paths": [test_path],
        "parallel": True,
        "timeout": 300
    }

    console.print()

    # Step 4: Behavior
    console.print("[bold yellow]Step 4:[/bold yellow] Auto-fix Behavior")
    console.print("When should deburger auto-apply fixes?\n")

    auto_threshold = Prompt.ask(
        "  Auto-apply if confidence >=",
        default="95"
    )

    config["fixes"] = {
        "auto_apply_threshold": int(auto_threshold),
        "ask_human_threshold": 80,
        "max_candidates": 3,
        "cache_enabled": True,
        "cache_path": "~/.deburger/cache.db"
    }

    console.print()

    # Step 5: GitHub
    console.print("[bold yellow]Step 5:[/bold yellow] GitHub Integration")

    use_github = Confirm.ask("Enable automatic PR creation?", default=True)
    if use_github:
        github_token = Prompt.ask("  GitHub personal access token", password=True)
        draft_threshold = Prompt.ask(
            "  Create draft PR if confidence <",
            default="90"
        )

        config["github"] = {
            "enabled": True,
            "token": f"${{{github_token}}}",
            "create_pr": True,
            "pr_labels": ["auto-fix", "deburger"],
            "draft_pr_threshold": int(draft_threshold)
        }
    else:
        config["github"] = {"enabled": False}

    console.print()

    # Step 6: Logging
    config["logging"] = {
        "level": "INFO",
        "directory": "~/.deburger/logs",
        "retention_days": 30,
        "structured": True
    }

    # Save config
    config_path = Path.cwd() / ".deburger.yaml"

    console.print("[bold yellow]Step 6:[/bold yellow] Save Configuration\n")
    console.print(f"Config will be saved to: [cyan]{config_path}[/cyan]")

    save = Confirm.ask("Save configuration?", default=True)

    if save:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print()
        console.print(Panel.fit(
            "[bold green]✓ Configuration saved![/bold green]\n\n"
            f"Config file: [cyan]{config_path}[/cyan]\n"
            "You can edit it manually anytime.\n\n"
            "Ready to go! Try: [yellow]deburger run[/yellow]",
            border_style="green"
        ))

        # Show next steps
        console.print()
        _show_next_steps(config)
    else:
        console.print("\n[yellow]Setup cancelled. Run 'deburger config' again anytime.[/yellow]")


def _show_next_steps(config: dict):
    """Show helpful next steps after config."""
    console.print("[bold]Quick tips:[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()

    table.add_row("deburger run", "Run tests and auto-fix bugs")
    table.add_row("deburger run --dry-run", "Preview fixes without applying")
    table.add_row("deburger run --no-pr", "Fix locally, no PR")

    console.print(table)
    console.print()
