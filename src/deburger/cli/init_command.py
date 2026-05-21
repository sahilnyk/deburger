"""Initialize deburger configuration."""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
import yaml

console = Console()


def run_init(provider: str, interactive: bool):
    """Initialize deburger in current directory."""

    config_path = Path(".deburger.yml")

    if config_path.exists():
        overwrite = Confirm.ask(
            ".deburger.yml already exists. Overwrite?",
            default=False
        )
        if not overwrite:
            console.print("[yellow]cancelled[/yellow]")
            return

    if interactive:
        config = _interactive_setup()
    else:
        config = _default_config(provider)

    # Write config
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Success message
    console.print()
    console.print(Panel(
        "[bold green]✓ config created![/bold green]\n\n"
        f"[dim]provider:[/dim] {provider}\n"
        f"[dim]config:[/dim] .deburger.yml\n\n"
        "[yellow]next steps:[/yellow]\n"
        "1. Configure cloud credentials\n"
        "2. Run: [cyan]deburger check[/cyan]\n"
        "3. Commit code and watch costs!",
        title="[bold]🍔 deburger initialized[/bold]",
        border_style="green",
        box=box.ROUNDED
    ))

    # Setup git hooks
    _setup_git_hooks()


def _default_config(provider: str) -> dict:
    """Generate default configuration."""

    config = {
        "version": "2.0",
        "providers": {
            "aws": {
                "enabled": provider == "aws",
                "region": "us-east-1",
                "profile": "default"
            },
            "gcp": {
                "enabled": provider == "gcp",
                "project_id": "${GCP_PROJECT_ID}",
                "region": "us-central1"
            },
            "azure": {
                "enabled": provider == "azure",
                "subscription_id": "${AZURE_SUBSCRIPTION_ID}",
                "region": "eastus"
            }
        },
        "budget": {
            "monthly_limit": 10000,
            "alert_threshold": 0.8,
            "block_threshold": 1.0,
            "deployment": {
                "max_increase_dollars": 500,
                "max_increase_percent": 20
            }
        },
        "traffic": {
            "requests_per_day": 100000,
            "avg_response_time_ms": 200,
            "peak_multiplier": 3.0
        },
        "analysis": {
            "languages": ["python", "javascript", "typescript", "go"],
            "ignore_patterns": [
                "node_modules/**",
                "venv/**",
                ".venv/**",
                "*.test.js",
                "test_*.py",
                "__pycache__/**"
            ],
            "detect": {
                "n_plus_one_queries": True,
                "sequential_async": True,
                "over_provisioned_resources": True,
                "missing_caching": True,
                "large_responses": True
            }
        },
        "hooks": {
            "pre_commit": {
                "enabled": True,
                "block_on_exceed": True,
                "show_fixes": True
            }
        },
        "optimize": {
            "auto_apply": False,
            "create_branch": True,
            "run_tests_after": True
        }
    }

    return config


def _interactive_setup() -> dict:
    """Interactive configuration setup."""

    console.print("\n🍔 [bold cyan]deburger setup wizard[/bold cyan]\n")

    # Cloud provider
    provider = Prompt.ask(
        "Cloud provider",
        choices=["aws", "gcp", "azure"],
        default="aws"
    )

    # Budget
    monthly_budget = Prompt.ask(
        "Monthly cloud budget (USD)",
        default="10000"
    )

    # Traffic
    requests_per_day = Prompt.ask(
        "Expected requests per day",
        default="100000"
    )

    # Build config
    config = _default_config(provider)
    config["budget"]["monthly_limit"] = int(monthly_budget)
    config["traffic"]["requests_per_day"] = int(requests_per_day)

    # Additional provider config
    if provider == "aws":
        region = Prompt.ask("AWS region", default="us-east-1")
        profile = Prompt.ask("AWS profile", default="default")
        config["providers"]["aws"]["region"] = region
        config["providers"]["aws"]["profile"] = profile

    elif provider == "gcp":
        project = Prompt.ask("GCP project ID")
        region = Prompt.ask("GCP region", default="us-central1")
        config["providers"]["gcp"]["project_id"] = project
        config["providers"]["gcp"]["region"] = region

    elif provider == "azure":
        subscription = Prompt.ask("Azure subscription ID")
        region = Prompt.ask("Azure region", default="eastus")
        config["providers"]["azure"]["subscription_id"] = subscription
        config["providers"]["azure"]["region"] = region

    return config


def _setup_git_hooks():
    """Setup git pre-commit hook."""

    git_dir = Path(".git")
    if not git_dir.exists():
        console.print("[dim]no git repo found - skipping hooks[/dim]")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    pre_commit = hooks_dir / "hooks" / "pre-commit"

    if pre_commit.exists():
        # Backup existing hook
        console.print("[dim]backing up existing pre-commit hook[/dim]")
        pre_commit.rename(pre_commit.with_suffix(".backup"))

    # Write hook
    hook_content = """#!/bin/bash
# deburger pre-commit hook
# Checks cloud costs before commit

echo "🍔 deburger checking costs..."

# Run deburger check on staged files
deburger check

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "⚠️  Cost check failed!"
    echo "Run 'deburger check --verbose' for details"
    echo ""
    exit 1
fi

exit 0
"""

    pre_commit.write_text(hook_content)
    pre_commit.chmod(0o755)

    console.print("[dim]✓ git pre-commit hook installed[/dim]")
