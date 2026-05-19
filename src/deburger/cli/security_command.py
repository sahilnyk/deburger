"""Security scan command."""

from pathlib import Path

from rich.console import Console

from deburger.security.scanner import SecurityScanner

console = Console()


def run_security_scan(path: str):
    console.print("[cyan]🔒 Running security scan...[/cyan]\n")

    scanner = SecurityScanner()
    all_vulns = []

    root = Path(path)
    python_files = list(root.rglob("*.py"))

    for filepath in python_files:
        try:
            content = filepath.read_text()
            vulns = scanner.scan_file(str(filepath), content)
            all_vulns.extend(vulns)
        except Exception:
            pass

    if not all_vulns:
        console.print("[green]✓ No vulnerabilities found[/green]")
        return

    console.print(f"[red]Found {len(all_vulns)} security issues:[/red]\n")

    by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for vuln in all_vulns:
        by_severity[vuln.severity.value].append(vuln)

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        issues = by_severity[severity]
        if not issues:
            continue

        color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}[severity]
        console.print(f"[{color}]{severity} ({len(issues)}):[/{color}]")

        for vuln in issues:
            console.print(f"  • {vuln.description}")
            console.print(f"    Line {vuln.line}: {vuln.code_snippet}")
            if vuln.fix_suggestion:
                console.print(f"    [dim]→ {vuln.fix_suggestion}[/dim]")
            console.print()
