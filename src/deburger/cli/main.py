import sys
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.align import Align
from pathlib import Path
from typing import Dict

app = typer.Typer(
    name="deburger",
    help="deburger - trim the fat from your cloud bill",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

SEVERITY_ICONS = {
    "critical": "[!]",
    "high": "[H]",
    "medium": "[M]",
    "low": "[L]",
}

PRICING_EVIDENCE: Dict[str, str] = {
    "aws": "AWS Lambda: $0.0000166667/GB-sec · RDS: $0.0000002/IO · S3: $0.0000004/req",
    "gcp": "Cloud Functions: $0.0000025/GB-sec · Cloud SQL: $0.0000003/IO",
    "azure": "Azure Functions: $0.000016/GB-sec · Cosmos DB: $0.00025/RU",
}


def cost_formula(issue_type: str) -> str:
    formulas = {
        "n_plus_one_query": "cost = queries × $0.0000002/IO",
        "sequential_async": "cost = requests × GB-sec × $0.0000166667",
        "over_provisioned_lambda": "cost = (current_mem - optimal_mem) × duration × requests × $0.0000166667",
        "missing_caching": "cost = (cache_misses × db_cost) + cache_service_fee",
        "s3_in_loop": "cost = total_requests × $0.0000004/request",
        "unbounded_query": "cost = (data_transfer + extra_compute) per request × requests",
        "expensive_logging": "cost = log_volume_GB × ($0.50/GB ingest + $0.03/GB storage)",
        "inefficient_query": "cost = requests × $0.000004/scan",
    }
    return formulas.get(issue_type, "cost = estimated_monthly_waste")


@app.callback(invoke_without_command=True)
def root(
    version: bool = typer.Option(False, "--version", help="Show version", is_eager=True),
):
    if version:
        from deburger import __version__
        console.print(Align.center(f"\n[bold cyan]🍔 deburger[/bold cyan] [dim]v{__version__}[/dim]\n"))
        raise typer.Exit()


@app.command()
def init(
    provider: str = typer.Option("aws", "--provider", "-p", help="Cloud provider: aws, gcp, azure"),
):
    """Initialize deburger in current project."""
    from deburger.config import generate_default_config

    config_path = Path(".deburger.yml")

    if config_path.exists():
        console.print("[yellow]config already exists[/yellow]")
        return

    config_content = generate_default_config()
    config_content = config_content.replace("provider: aws", f"provider: {provider}")
    config_path.write_text(config_content)
    console.print(f"[green]created .deburger.yml[/green] (provider: {provider})")
    console.print("[dim]run 'deburger check' to start scanning[/dim]")


@app.command()
def check(
    path: str = typer.Argument(".", help="Path to analyze"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed breakdown"),
    incremental: bool = typer.Option(
        True,
        "--incremental/--full",
        help="Scan Git changes only or scan every supported file",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """Scan code and predict cloud costs."""
    has_issues = asyncio.run(_check(path, verbose, incremental, json_output))
    if has_issues:
        raise typer.Exit(code=1)


async def _check(path: str, verbose: bool, incremental: bool, json_output: bool = False) -> bool:
    from deburger.config import load_config
    from deburger.scanner import FastScanner
    from deburger.cost import CostEngine, TrafficEstimate
    from deburger.providers import ProviderRegistry

    config = load_config()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("scanning code...", total=None)
        scanner = FastScanner(config.to_dict(), max_workers=config.performance["max_workers"])
        issues = await scanner.scan_path(path, incremental=incremental)
        progress.update(task, description=f"found {len(issues)} issues")

        if not issues:
            progress.stop()
            console.print("\n[green]✓ no expensive patterns found[/green]")
            return False

        progress.update(task, description="calculating costs...")
        provider = ProviderRegistry.get(config.provider)
        results = None
        if provider:
            await provider.initialize({"region": config.region})
            engine = CostEngine(provider, config.region)
            await engine.preload_pricing()
            traffic = TrafficEstimate.from_config(config.to_dict())
            results = await engine.calculate_total_savings(issues, traffic)

    if json_output:
        import json
        output = {
            "issues": [
                {
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "monthly_cost": float(issue.estimated_monthly_cost),
                    "savings": float(issue.savings_monthly) if issue.savings_monthly else 0,
                    "fix": issue.fix_suggestion,
                }
                for issue in issues
            ],
            "summary": {
                "total_issues": len(issues),
                "total_monthly_cost": float(results["total_savings"]) if results else 0,
                "savings_percentage": results["savings_percentage"] if results else 0,
            },
        }
        print(json.dumps(output, indent=2))
        return True

    console.print()
    provider_name = config.provider
    evidence_line = PRICING_EVIDENCE.get(provider_name, "")
    if evidence_line:
        console.print(f"[dim]pricing source: {evidence_line}[/dim]")
        console.print()

    table = Table(
        title="Expensive Code Patterns Detected",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("file", style="dim", no_wrap=True)
    table.add_column("line", justify="right", style="dim")
    table.add_column("pattern", style="bold", no_wrap=True)
    table.add_column("severity", no_wrap=True)
    table.add_column("monthly cost", justify="right", style="yellow", no_wrap=True)
    table.add_column("savings", justify="right", style="green", no_wrap=True)

    for issue in issues:
        color = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "dim",
        }.get(issue.severity.value, "dim")
        icon = SEVERITY_ICONS.get(issue.severity.value, "")

        table.add_row(
            str(Path(issue.file_path).name),
            str(issue.line_number),
            issue.type.value.replace("_", " "),
            f"[{color}]{icon} {issue.severity.value}[/{color}]",
            f"${issue.estimated_monthly_cost:.2f}",
            f"${issue.savings_monthly:.2f}" if issue.savings_monthly else "-",
        )

    console.print(table)

    if results:
        console.print()
        total_cost = results['total_savings']
        total_after = results['total_optimized_cost']
        savings_pct = results['savings_percentage']

        top_text = f"[bold]Monthly Waste:[/bold]  [red]${total_cost:.2f}[/red]  →  [green]${total_after:.2f}[/green]"
        console.print(Panel(top_text, border_style="cyan", padding=(0, 2)))

        bottom_items = [f"[bold green]Savings: {savings_pct:.0f}%[/bold green]"]
        if results.get("by_resource_type"):
            for rt, v in sorted(results["by_resource_type"].items(), key=lambda x: x[1]["savings"], reverse=True):
                bottom_items.append(f"  • {rt}: [yellow]${v['savings']:.2f}[/yellow] ({v['count']} issue{'s' if v['count'] > 1 else ''})")
        console.print(Panel("\n".join(bottom_items), border_style="green", padding=(0, 2)))

    if verbose:
        console.print()
        for i, issue in enumerate(issues, 1):
            header = Text()
            header.append(f"[{i}/{len(issues)}] ", style="dim cyan")
            header.append(f"{Path(issue.file_path).name}", style="bold yellow")
            header.append(f":{issue.line_number} ", style="bright_blue")
            header.append(f"({issue.type.value.replace('_', ' ')})", style="red")
            console.print(header)

            info_text = (
                f"[dim]{issue.explanation}[/dim]\n\n"
                f"[bold]Formula:[/bold] [italic]{cost_formula(issue.type.value)}[/italic]\n"
                f"[bold]Monthly waste:[/bold] [red]${issue.estimated_monthly_cost:.2f}[/red]\n"
                f"[bold]Savings:[/bold] [green]${issue.savings_monthly:.2f}/mo[/green]" if issue.savings_monthly else "[dim]Savings: N/A[/dim]"
            )
            console.print(Panel(info_text, border_style="blue", padding=(1, 2)))

            if issue.fix_suggestion:
                fix_text = f"[bold]Suggested Fix:[/bold]\n{issue.fix_suggestion}"
                console.print(Panel(fix_text, border_style="green", padding=(1, 2)))

            console.print()

    return True


@app.command()
def optimize(
    path: str = typer.Argument(".", help="Path to optimize"),
    auto_apply: bool = typer.Option(False, "--auto-apply", help="Apply safe fixes automatically"),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Preview fixes or write them to disk",
    ),
):
    """Find and fix expensive code patterns."""
    asyncio.run(_optimize(path, auto_apply, dry_run))


async def _optimize(path: str, auto_apply: bool, dry_run: bool):
    from deburger.config import load_config
    from deburger.scanner import FastScanner
    from deburger.optimizer import CodeFixer, FixApplier

    config = load_config()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("scanning for optimizations...", total=None)
        scanner = FastScanner(config.to_dict())
        issues = await scanner.scan_path(path, incremental=False)

        if not issues:
            progress.stop()
            console.print("\n[green]✓ nothing to optimize[/green]")
            return

        progress.update(task, description=f"generating fixes for {len(issues)} issues...")

        file_contents = {}
        for issue in issues:
            if issue.file_path not in file_contents:
                try:
                    with open(issue.file_path, 'r', encoding='utf-8') as f:
                        file_contents[issue.file_path] = f.read()
                except Exception:
                    pass

        fixer = CodeFixer()
        fixes = await fixer.generate_all_fixes(issues, file_contents)

    if not fixes:
        console.print("\n[yellow]found issues but couldn't auto-generate fixes[/yellow]")
        console.print("[dim]run 'deburger check -v' for manual suggestions[/dim]")
        return

    console.print()
    table = Table(
        title="Optimization Suggestions",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("file", style="dim")
    table.add_column("fix")
    table.add_column("confidence", justify="right")
    table.add_column("savings/mo", justify="right", style="yellow")
    table.add_column("auto-safe")

    for fix in fixes:
        table.add_row(
            str(Path(fix.issue.file_path).name) + f":{fix.issue.line_number}",
            fix.explanation,
            f"{fix.confidence * 100:.0f}%",
            f"${fix.savings_monthly:.2f}",
            "[green]✓[/green]" if fix.auto_apply_safe else "[red]✗[/red]",
        )

    console.print(table)

    total_savings = sum(f.savings_monthly for f in fixes)
    safe_fixes = sum(1 for f in fixes if f.auto_apply_safe)

    summary_text = (
        f"[bold cyan]Total Potential Savings:[/bold cyan] [green]${total_savings:.2f}/mo[/green]\n"
        f"[bold cyan]Safe Auto-Fixes:[/bold cyan] [green]{safe_fixes}/{len(fixes)}[/green]"
    )
    console.print(f"\n{Panel(summary_text, border_style='green', padding=(1, 2))}")

    if auto_apply or not dry_run:
        applier = FixApplier(dry_run=dry_run)
        results = await applier.apply_fixes(fixes, auto_only=auto_apply)

        if dry_run:
            console.print(f"\n[dim]dry run - {results['applied']} fixes would be applied[/dim]")
        else:
            console.print(f"\n[green]✓ applied {results['applied']} fixes[/green]")
            if results['failed'] > 0:
                console.print(f"[red]{results['failed']} fixes failed validation[/red]")
    else:
        console.print("\n[dim]run with --apply to apply fixes[/dim]")


@app.command()
def diff(
    base: str = typer.Argument("main", help="Base branch/commit"),
    head: str = typer.Argument("HEAD", help="Target branch/commit"),
):
    """Compare costs between branches."""
    asyncio.run(_diff(base, head))


async def _diff(base: str, head: str):
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            console.print(f"[red]git diff failed: {result.stderr}[/red]")
            return
        changed_files = [f for f in result.stdout.strip().split("\n") if f]
    except Exception as e:
        console.print(f"[red]error: {e}[/red]")
        return

    if not changed_files:
        console.print("[green]no changes between branches[/green]")
        return

    from deburger.config import load_config
    from deburger.scanner import FastScanner

    config = load_config()
    scanner = FastScanner(config.to_dict())

    issues = []
    for f in changed_files:
        if Path(f).exists():
            file_issues = await scanner.scan_path(f, incremental=False)
            issues.extend(file_issues)

    console.print(f"\n[bold]{base}[/bold] [dim]→[/dim] [bold]{head}[/bold]")
    console.print(f"[dim]{len(changed_files)} files changed[/dim]")

    if issues:
        total_cost = sum(i.estimated_monthly_cost for i in issues)
        critical = sum(1 for i in issues if i.severity.value == "critical")

        panel_text = (
            f"[bold red]New Expensive Patterns:[/bold red] {len(issues)} found\n"
            f"[bold]Cost Impact:[/bold] [red]+${total_cost:.2f}/mo[/red]"
        )
        if critical > 0:
            panel_text = f"[bold red]CRITICAL:[/bold red] {critical}\n" + panel_text

        console.print(Panel(panel_text, border_style="red", title="[bold red]PR Analysis[/bold red]"))

        tree = Tree(f"[bold cyan]{len(changed_files)} files changed[/bold cyan]")
        for issue in sorted(issues, key=lambda x: x.estimated_monthly_cost, reverse=True)[:5]:
            sev_icon = SEVERITY_ICONS.get(issue.severity.value, "")
            tree.add(f"{sev_icon} {Path(issue.file_path).name}:{issue.line_number} {issue.type.value.replace('_', ' ')} [yellow]${issue.estimated_monthly_cost:.2f}[/yellow]")
        if len(issues) > 5:
            tree.add(f"[dim]... and {len(issues) - 5} more[/dim]")
        console.print(tree)
    else:
        console.print("\n[green]no new expensive patterns[/green]")


@app.command()
def hook(
    install: bool = typer.Option(False, "--install", help="Install git pre-commit hook"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Remove git hook"),
):
    """Manage git hooks."""
    from deburger.hooks import install_hook, uninstall_hook

    if install:
        install_hook()
        console.print("[green]pre-commit hook installed[/green]")
        console.print("[dim]deburger will run on every commit[/dim]")
    elif uninstall:
        uninstall_hook()
        console.print("[yellow]pre-commit hook removed[/yellow]")
    else:
        console.print("[dim]use --install or --uninstall[/dim]")


@app.command(name="pr-comment")
def pr_comment(
    pr: int = typer.Argument(..., help="PR number"),
    base: str = typer.Option("main", "--base", help="Base branch"),
):
    """Post cost impact comment on a GitHub PR."""
    asyncio.run(_pr_comment(pr, base))


async def _pr_comment(pr: int, base: str):
    from deburger.integrations import generate_pr_comment, post_pr_comment

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("analyzing PR cost impact...", total=None)
        comment = await generate_pr_comment(base=base)

    if not comment:
        console.print("[green]no cost impact detected[/green]")
        return

    console.print(comment)
    post_pr_comment(pr, comment)
    console.print(f"\n[green]comment posted on PR #{pr}[/green]")


@app.command()
def blame(
    path: str = typer.Argument(".", help="Path to analyze"),
    top: int = typer.Option(10, "--top", "-n", help="Number of devs to show"),
):
    """Show who's costing the most (git blame + cost analysis)."""
    asyncio.run(_blame(path, top))


async def _blame(path: str, top: int):
    from deburger.config import load_config
    from deburger.scanner import FastScanner
    from deburger.integrations.blame import get_cost_leaderboard

    config = load_config()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("scanning + blaming...", total=None)
        scanner = FastScanner(config.to_dict())
        issues = await scanner.scan_path(path, incremental=False)

    if not issues:
        console.print("[green]no expensive patterns found[/green]")
        return

    leaderboard = get_cost_leaderboard(issues)

    table = Table(
        title="Cost Leaderboard",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        caption="who's costing the most",
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("developer")
    table.add_column("issues", justify="right")
    table.add_column("monthly cost", justify="right", style="red")
    table.add_column("worst issue", style="dim")

    for rank, report in enumerate(leaderboard[:top], 1):
        worst = report.worst_issue.description if report.worst_issue else "-"
        table.add_row(
            str(rank),
            report.author,
            str(report.issues_introduced),
            f"${report.total_monthly_cost:.2f}",
            worst,
        )

    console.print()
    console.print(table)

    total = sum(r.total_monthly_cost for r in leaderboard)

    medals = ["🥇", "🥈", "🥉"]
    top_devs = "\n".join(
        f"{medals[i] if i < 3 else '  '} {r.author}: [red]${r.total_monthly_cost:.2f}[/red]"
        for i, r in enumerate(leaderboard[:3])
    )
    if top_devs:
        console.print(Panel(top_devs, border_style="yellow", padding=(0, 2)))
    console.print(Panel(f"[bold][red]Total Waste:[/red] ${total:.2f}/month[/bold]", border_style="red", padding=(0, 2)))


@app.command()
def version():
    """Show version."""
    from deburger import __version__
    console.print(f"🍔 deburger v{__version__}")


def main():
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {e}",
            border_style="red",
            padding=(1, 2),
            title="[bold red]Failed[/bold red]"
        )
        console.print(error_panel)
        sys.exit(1)


if __name__ == "__main__":
    main()
