"""Initialize command implementation."""

import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


def run_init(requirement: str):
    console.print("[cyan]🍔 Initializing deburger...[/cyan]\n")

    config_content = f"""# deburger configuration
requirement: "{requirement}"

sub_goals:
  - id: core
    description: "Implement core functionality"
    weight: 40
  - id: testing
    description: "Add comprehensive tests"
    weight: 30
  - id: security
    description: "Security hardening"
    weight: 20
  - id: docs
    description: "Documentation"
    weight: 10

llm:
  provider: openai
  api_key: ${{OPENAI_API_KEY}}
  model: gpt-4

  guardrails:
    - "Never disable security features"
    - "Always validate user input"
    - "Prefer explicit over implicit"
    - "No hardcoded credentials"

  prompts:
    guidance: |
      You are {{progress}}% toward the goal.
      Next focus: {{next_focus}}
      Security issues: {{security_count}}

security:
  enabled: true
  fail_on_high: true
  ignore_patterns:
    - tests/
    - docs/

metrics:
  min_quality_score: 70
  max_complexity: 10
"""

    config_path = Path(".deburger.yml")
    if config_path.exists():
        if not Confirm.ask(f"[yellow]{config_path} exists. Overwrite?[/yellow]"):
            console.print("[red]Aborted[/red]")
            return

    config_path.write_text(config_content)
    console.print(f"[green]✓ Created {config_path}[/green]")

    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text()
        if ".deburger.cache" not in gitignore:
            with gitignore_path.open("a") as f:
                f.write("\n.deburger.cache\n")
            console.print("[green]✓ Updated .gitignore[/green]")

    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("1. Set your API key: export OPENAI_API_KEY=...")
    console.print("2. Make code changes")
    console.print("3. Run: deburger analyze")
