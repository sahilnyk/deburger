import subprocess
from typing import Optional
from pathlib import Path

from deburger.config import load_config
from deburger.scanner import FastScanner
from deburger.cost import CostEngine, TrafficEstimate
from deburger.providers.registry import ProviderRegistry


async def generate_pr_comment(base: str = "main", head: str = "HEAD") -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True,
            text=True,
            timeout=10,
        )
        changed_files = [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        return ""

    if not changed_files:
        return ""

    config = load_config()
    scanner = FastScanner(config.to_dict())

    issues = []
    for f in changed_files:
        if Path(f).exists():
            file_issues = await scanner.scan_path(f, incremental=False)
            issues.extend(file_issues)

    if not issues:
        return "## deburger\n\n**No expensive patterns detected.** Ship it.\n"

    provider = ProviderRegistry.get(config.provider)
    if provider:
        await provider.initialize({"region": config.region})
        engine = CostEngine(provider, config.region)
        await engine.preload_pricing()
        traffic = TrafficEstimate.from_config(config.to_dict())
        results = await engine.calculate_total_savings(issues, traffic)
        total_cost = results["total_savings"]
    else:
        total_cost = sum(i.estimated_monthly_cost for i in issues)

    comment = "## deburger cost impact\n\n"

    if total_cost > 500:
        comment += f"**This PR adds ~${total_cost:.0f}/month** to your cloud bill.\n\n"
    elif total_cost > 100:
        comment += f"**Estimated cost impact: +${total_cost:.0f}/month**\n\n"
    else:
        comment += f"Minor cost impact: +${total_cost:.2f}/month\n\n"

    comment += "| File | Issue | Severity | Cost/mo |\n"
    comment += "|------|-------|----------|--------|\n"

    for issue in issues[:10]:
        file_name = Path(issue.file_path).name
        comment += f"| `{file_name}:{issue.line_number}` | {issue.description} | {issue.severity.value} | ${issue.estimated_monthly_cost:.2f} |\n"

    if len(issues) > 10:
        comment += f"\n*...and {len(issues) - 10} more issues*\n"

    comment += f"\n**Total potential savings: ${total_cost:.2f}/month**\n"
    comment += "\nRun `deburger optimize` to auto-fix these issues.\n"

    return comment


def post_pr_comment(pr_number: int, comment: str, repo: Optional[str] = None):
    if not repo:
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            repo = result.stdout.strip()
        except Exception:
            return

    try:
        subprocess.run(
            ["gh", "pr", "comment", str(pr_number), "--body", comment],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        pass
