import sys
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

app = typer.Typer(
    name="deburger",
    help="deburger - trim the fat from your cloud bill",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version", is_eager=True),
):
    if version:
        from deburger import __version__

        console.print(f"deburger v{__version__}")
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

    # override provider
    config_content = config_content.replace("provider: aws", f"provider: {provider}")

    config_path.write_text(config_content)
    console.print(f"[green]created .deburger.yml[/green] (provider: {provider})")
    console.print("[dim]run 'deburger check' to start scanning[/dim]")


@app.command()
def check(
    path: str = typer.Argument(".", help="Path to analyze"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed breakdown"),
    incremental: bool = typer.Option(True, "--incremental/--full", help="Only scan changed files"),
):
    """Scan code and predict cloud costs."""
    has_issues = asyncio.run(_check(path, verbose, incremental))
    if has_issues:
        raise typer.Exit(code=1)


async def _check(path: str, verbose: bool, incremental: bool) -> bool:
    from deburger.config import load_config
    from deburger.scanner import FastScanner
    from deburger.cost import CostEngine, TrafficEstimate
    from deburger.providers.registry import ProviderRegistry

    config = load_config()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # scan
        task = progress.add_task("scanning code...", total=None)
        scanner = FastScanner(config.to_dict(), max_workers=config.performance["max_workers"])
        issues = await scanner.scan_path(path, incremental=incremental)
        progress.update(task, description=f"found {len(issues)} issues")

        if not issues:
            progress.stop()
            console.print("\n[green]no expensive patterns found - ur good[/green]")
            return False

        # calculate costs
        progress.update(task, description="calculating costs...")
        provider = ProviderRegistry.get(config.provider)
        if provider:
            await provider.initialize({"region": config.region})
            engine = CostEngine(provider, config.region)
            await engine.preload_pricing()
            traffic = TrafficEstimate.from_config(config.to_dict())
            results = await engine.calculate_total_savings(issues, traffic)
        else:
            results = None

    # display results
    console.print()

    table = Table(title="issues found", show_header=True, header_style="bold cyan")
    table.add_column("file", style="dim")
    table.add_column("line", justify="right")
    table.add_column("type", style="red")
    table.add_column("severity")
    table.add_column("monthly cost", justify="right", style="yellow")
    table.add_column("savings", justify="right", style="green")

    for issue in issues:
        severity_color = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "dim",
        }.get(issue.severity.value, "dim")

        table.add_row(
            str(Path(issue.file_path).name),
            str(issue.line_number),
            issue.type.value.replace("_", " "),
            f"[{severity_color}]{issue.severity.value}[/{severity_color}]",
            f"${issue.estimated_monthly_cost:.2f}",
            f"${issue.savings_monthly:.2f}" if issue.savings_monthly else "-",
        )

    console.print(table)

    if results:
        console.print()
        console.print(Panel(
            f"[bold]total monthly waste:[/bold] [red]${results['total_savings']:.2f}[/red]\n"
            f"[bold]after optimization:[/bold] [green]${results['total_optimized_cost']:.2f}[/green]\n"
            f"[bold]savings:[/bold] [cyan]{results['savings_percentage']:.0f}%[/cyan]",
            title="cost summary",
            border_style="cyan",
        ))

    if verbose:
        console.print()
        for issue in issues:
            console.print(f"\n[bold]{issue.file_path}:{issue.line_number}[/bold]")
            console.print(f"[dim]{issue.explanation}[/dim]")
            if issue.fix_suggestion:
                console.print(f"[green]fix:[/green] {issue.fix_suggestion}")

    return True


@app.command()
def optimize(
    path: str = typer.Argument(".", help="Path to optimize"),
    auto_apply: bool = typer.Option(False, "--auto-apply", help="Apply safe fixes automatically"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview fixes without applying"),
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
            console.print("\n[green]nothing to optimize - code is clean[/green]")
            return

        progress.update(task, description=f"generating fixes for {len(issues)} issues...")

        # read file contents for all affected files
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
        console.print("[dim]check output of 'deburger check -v' for manual suggestions[/dim]")
        return

    # show fixes
    console.print()
    table = Table(title="optimizations", show_header=True, header_style="bold cyan")
    table.add_column("file", style="dim")
    table.add_column("fix", style="green")
    table.add_column("confidence", justify="right")
    table.add_column("savings/mo", justify="right", style="yellow")
    table.add_column("auto-safe")

    for fix in fixes:
        table.add_row(
            str(Path(fix.issue.file_path).name) + f":{fix.issue.line_number}",
            fix.explanation,
            f"{fix.confidence * 100:.0f}%",
            f"${fix.savings_monthly:.2f}",
            "[green]yes[/green]" if fix.auto_apply_safe else "[red]no[/red]",
        )

    console.print(table)

    total_savings = sum(f.savings_monthly for f in fixes)
    console.print(f"\n[bold]total potential savings:[/bold] [green]${total_savings:.2f}/mo[/green]")

    # apply if requested
    if auto_apply or not dry_run:
        applier = FixApplier(dry_run=dry_run)
        results = await applier.apply_fixes(fixes, auto_only=auto_apply)

        if dry_run:
            console.print(f"\n[dim]dry run - {results['applied']} fixes would be applied[/dim]")
        else:
            console.print(f"\n[green]applied {results['applied']} fixes[/green]")
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

    # get changed files between branches
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

    # scan only changed files that exist
    issues = []
    for f in changed_files:
        if Path(f).exists():
            file_issues = await scanner.scan_path(f, incremental=False)
            issues.extend(file_issues)

    console.print(f"\n[bold]{base}[/bold] -> [bold]{head}[/bold]")
    console.print(f"[dim]{len(changed_files)} files changed[/dim]")

    if issues:
        total_cost = sum(i.estimated_monthly_cost for i in issues)
        console.print(f"\n[red]new issues: {len(issues)}[/red]")
        console.print(f"[red]estimated cost impact: ${total_cost:.2f}/mo[/red]")

        for issue in issues:
            console.print(f"  [dim]{issue.file_path}:{issue.line_number}[/dim] - {issue.type.value}")
    else:
        console.print("\n[green]no new expensive patterns introduced[/green]")


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
        task = progress.add_task("analyzing PR cost impact...", total=None)
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
        task = progress.add_task("scanning + blaming...", total=None)
        scanner = FastScanner(config.to_dict())
        issues = await scanner.scan_path(path, incremental=False)

    if not issues:
        console.print("[green]no expensive patterns found[/green]")
        return

    leaderboard = get_cost_leaderboard(issues)

    table = Table(title="cost leaderboard (who's burning money)", show_header=True, header_style="bold cyan")
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
    console.print(f"\n[bold]total waste:[/bold] [red]${total:.2f}/month[/red]")


@app.command()
def version():
    """Show version."""
    from deburger import __version__
    console.print(f"deburger v{__version__}")


def main():
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
