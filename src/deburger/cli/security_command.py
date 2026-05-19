"""Security scan command with beautiful UI."""

from pathlib import Path

from deburger.security.scanner import SecurityScanner
from deburger.ui.display import ui


def run_security_scan(path: str):
    ui.header("Running security scan...")

    scanner = SecurityScanner()
    all_vulns = []

    root = Path(path)
    python_files = list(root.rglob("*.py"))

    with ui.progress_bar("Scanning files...") as progress:
        task = progress.add_task("Scanning...", total=len(python_files))

        for filepath in python_files:
            try:
                content = filepath.read_text()
                vulns = scanner.scan_file(str(filepath), content)
                all_vulns.extend(vulns)
            except Exception:
                pass
            progress.update(task, advance=1)

    ui.console.print()

    if not all_vulns:
        ui.success("No vulnerabilities found")
        return

    ui.console.print(ui.security_issues_panel(all_vulns))
    ui.console.print()

    by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for vuln in all_vulns:
        by_severity[vuln.severity.value].append(vuln)

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        issues = by_severity[severity]
        if not issues:
            continue

        color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}[severity]
        ui.console.print(f"[{color}]{severity} ({len(issues)}):[/{color}]")

        for vuln in issues[:5]:
            ui.console.print(f"  • {vuln.description}")
            ui.console.print(f"    [dim]Line {vuln.line}: {vuln.code_snippet[:60]}...[/dim]")
            if vuln.fix_suggestion:
                ui.console.print(f"    [dim]→ {vuln.fix_suggestion}[/dim]")
            ui.console.print()
