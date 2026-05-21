"""Beautiful CLI display components."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.layout import Layout
from rich import box

console = Console()


class DeburgerUI:
    def __init__(self):
        self.console = Console()

    def header(self, text: str):
        self.console.print(f"\n[bold cyan]{text}[/bold cyan]\n")

    def success(self, text: str):
        self.console.print(f"[green]✓[/green] {text}")

    def error(self, text: str):
        self.console.print(f"[red]✗[/red] {text}")

    def warning(self, text: str):
        self.console.print(f"[yellow]warning:[/yellow] {text}")

    def info(self, text: str):
        self.console.print(f"[cyan]info:[/cyan] {text}")

    def progress_bar(self, description: str):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

    def requirement_panel(self, requirement: str, progress: float):
        content = (
            f"[bold]Requirement:[/bold] {requirement}\n"
            f"[bold]Progress:[/bold] {self._progress_bar_text(progress)}"
        )
        return Panel(content, title="Requirement Progress", border_style="green", box=box.ROUNDED)

    def _progress_bar_text(self, progress: float) -> str:
        filled = int(progress * 20)
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        percentage = f"{progress:.0%}"

        if progress < 0.3:
            color = "red"
            vibe = "just getting started"
        elif progress < 0.5:
            color = "yellow"
            vibe = "making moves"
        elif progress < 0.8:
            color = "yellow"
            vibe = "grinding"
        elif progress < 0.95:
            color = "green"
            vibe = "almost there"
        else:
            color = "green"
            vibe = "crushing it"

        return f"[{color}]{bar}[/{color}] {percentage} [dim]({vibe})[/dim]"

    def subgoals_table(self, subgoals: list):
        table = Table(title="Sub-Goals Progress", box=box.ROUNDED)
        table.add_column("Goal", style="cyan", no_wrap=False)
        table.add_column("Progress", justify="center", style="green", width=12)
        table.add_column("Status", justify="center", style="yellow", width=8)

        for goal in subgoals:
            status = "✓" if goal.completion >= 0.9 else "..." if goal.completion >= 0.5 else "○"
            progress_bar = self._mini_progress_bar(goal.completion)
            table.add_row(goal.description, progress_bar, status)

        return table

    def _mini_progress_bar(self, completion: float) -> str:
        filled = int(completion * 10)
        empty = 10 - filled
        bar = "▰" * filled + "▱" * empty
        return f"{bar} {completion:.0%}"

    def security_issues_panel(self, issues: list):
        if not issues:
            return Panel("[green]✓ No security issues found[/green]", title="Security", border_style="green", box=box.ROUNDED)

        tree = Tree("Security Issues", guide_style="red")

        high = [i for i in issues if i.severity.value == "HIGH"]
        medium = [i for i in issues if i.severity.value == "MEDIUM"]
        low = [i for i in issues if i.severity.value == "LOW"]

        if high:
            high_node = tree.add(f"[red]HIGH ({len(high)})[/red]")
            for issue in high[:3]:
                high_node.add(f"{issue.description} (line {issue.line})")
                if issue.fix_suggestion:
                    high_node.add(f"[dim]→ {issue.fix_suggestion}[/dim]")

        if medium:
            med_node = tree.add(f"[yellow]MEDIUM ({len(medium)})[/yellow]")
            for issue in medium[:2]:
                med_node.add(f"{issue.description} (line {issue.line})")

        if low:
            tree.add(f"[blue]LOW ({len(low)})[/blue]")

        return Panel(tree, title=f"Security ({len(issues)} issues)", border_style="red", box=box.ROUNDED)

    def code_diff(self, filepath: str, old_code: str, new_code: str):
        syntax = Syntax(new_code, "python", theme="monokai", line_numbers=True)
        return Panel(syntax, title=filepath, border_style="blue", box=box.ROUNDED)

    def metrics_summary(self, quality_score: float, complexity: int, loc: int):
        layout = Layout()

        quality_color = "green" if quality_score >= 80 else "yellow" if quality_score >= 60 else "red"
        complexity_color = "green" if complexity <= 10 else "yellow" if complexity <= 20 else "red"

        content = (
            f"[bold]Quality Score:[/bold] [{quality_color}]{quality_score:.0f}/100[/{quality_color}]\n"
            f"[bold]Complexity:[/bold] [{complexity_color}]{complexity}[/{complexity_color}]\n"
            f"[bold]Lines of Code:[/bold] {loc}"
        )

        return Panel(content, title="Code Metrics", border_style="cyan", box=box.ROUNDED)

    def guidance_panel(self, guidance: str):
        return Panel(
            guidance,
            title="AI Guidance",
            border_style="magenta",
            box=box.DOUBLE
        )

    def summary_stats(self, files_changed: int, lines_added: int, lines_removed: int):
        return (
            f"[cyan]Files:[/cyan] {files_changed} | "
            f"[green]+{lines_added}[/green] | "
            f"[red]-{lines_removed}[/red]"
        )


ui = DeburgerUI()
