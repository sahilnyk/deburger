"""Initialize command with interactive prompts."""

import os
from pathlib import Path

from deburger.ui.display import ui


def run_init(requirement: str):
    ui.header("Initializing deburger...")

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
      You are {{{{progress}}}}% toward the goal.
      Next focus: {{{{next_focus}}}}
      Security issues: {{{{security_count}}}}

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
        ui.warning(f"{config_path} already exists")
        return

    config_path.write_text(config_content)
    ui.success(f"Created {config_path}")

    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text()
        if ".deburger.cache" not in gitignore:
            with gitignore_path.open("a") as f:
                f.write("\n.deburger.cache\n")
            ui.success("Updated .gitignore")

    ui.console.print("\n[cyan]Next steps:[/cyan]")
    ui.info("Set your API key: export OPENAI_API_KEY=...")
    ui.info("Make code changes")
    ui.info("Run: deburger analyze")
