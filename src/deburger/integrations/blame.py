import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal

from deburger.analyzers.base import Issue


@dataclass
class BlameEntry:
    author: str
    email: str
    commit: str
    date: str
    line: int


@dataclass
class DeveloperCostReport:
    author: str
    email: str
    issues_introduced: int
    total_monthly_cost: Decimal
    worst_issue: Optional[Issue]
    commits: List[str]


def get_blame_for_line(file_path: str, line_number: int) -> Optional[BlameEntry]:
    # git blame for specific line
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line_number},{line_number}", "--porcelain", file_path],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        output = result.stdout
        commit = output.split('\n')[0].split(' ')[0]
        author = ""
        email = ""
        date = ""

        for line in output.split('\n'):
            if line.startswith('author '):
                author = line[7:]
            elif line.startswith('author-mail '):
                email = line[12:].strip('<>')
            elif line.startswith('author-time '):
                date = line[12:]

        return BlameEntry(
            author=author,
            email=email,
            commit=commit,
            date=date,
            line=line_number
        )

    except Exception:
        return None


def blame_issues(issues: List[Issue]) -> Dict[str, DeveloperCostReport]:
    # blame all issues and group by developer
    developer_map: Dict[str, DeveloperCostReport] = {}

    for issue in issues:
        blame = get_blame_for_line(issue.file_path, issue.line_number)

        if not blame:
            continue

        key = blame.email or blame.author

        if key not in developer_map:
            developer_map[key] = DeveloperCostReport(
                author=blame.author,
                email=blame.email,
                issues_introduced=0,
                total_monthly_cost=Decimal("0"),
                worst_issue=None,
                commits=[],
            )

        report = developer_map[key]
        report.issues_introduced += 1
        report.total_monthly_cost += issue.estimated_monthly_cost

        if blame.commit not in report.commits:
            report.commits.append(blame.commit)

        # track worst issue
        if report.worst_issue is None or issue.estimated_monthly_cost > report.worst_issue.estimated_monthly_cost:
            report.worst_issue = issue

    return developer_map


def get_cost_leaderboard(issues: List[Issue]) -> List[DeveloperCostReport]:
    # sorted by who's costing the most
    reports = blame_issues(issues)
    return sorted(reports.values(), key=lambda r: r.total_monthly_cost, reverse=True)
