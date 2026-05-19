"""AI guidance command."""

import os
from rich.console import Console

from deburger.llm.client import LLMClient, LLMConfig

console = Console()


def run_guidance():
    console.print("[cyan]🤖 Generating AI guidance...[/cyan]\n")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENAI_API_KEY not set[/red]")
        return

    config = LLMConfig(
        provider="openai",
        api_key=api_key,
        model="gpt-4",
        guardrails=[
            "Never disable security features",
            "Always validate user input",
            "No hardcoded credentials",
        ],
    )

    client = LLMClient(config)

    context = {
        "progress": 75,
        "security_count": 2,
        "next_focus": "Input validation",
    }

    guidance = client.generate_guidance(context)
    console.print("[green]Guidance:[/green]")
    console.print(guidance)
