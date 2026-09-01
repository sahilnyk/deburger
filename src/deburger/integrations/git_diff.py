"""Read and compare source files from Git revisions."""

import subprocess
from typing import List, Optional, Tuple

from deburger.analyzers.base import Issue
from deburger.analyzers.registry import AnalyzerRegistry

def parse_revision_range(base: str, head: str) -> Tuple[str, str]:
    if ".." in base and head == "HEAD":
        left, right = base.split("..", 1)
        if left and right:
            return left, right
    return base, head


def changed_files(base: str, head: str) -> List[str]:
    result = _run_git("diff", "--name-only", "--diff-filter=ACMR", base, head)
    return [line for line in result.splitlines() if line]


def read_file(revision: str, file_path: str) -> Optional[str]:
    result = subprocess.run(
        ["git", "show", f"{revision}:{file_path}"],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def added_issues(base: str, head: str, config: dict) -> List[Issue]:
    added = []
    for file_path in changed_files(base, head):
        analyzer = AnalyzerRegistry.get_for_file(file_path)
        if analyzer is None:
            continue

        base_code = read_file(base, file_path)
        head_code = read_file(head, file_path)
        if head_code is None:
            continue

        base_issues = analyzer.analyze(file_path, base_code or "", config)
        head_issues = analyzer.analyze(file_path, head_code, config)
        remaining = [_fingerprint(issue) for issue in base_issues]

        for issue in head_issues:
            fingerprint = _fingerprint(issue)
            if fingerprint in remaining:
                remaining.remove(fingerprint)
            else:
                added.append(issue)
    return added


def _fingerprint(issue: Issue) -> Tuple[str, str]:
    normalized = " ".join(issue.code_snippet.split())
    return issue.type.value, normalized


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "git command failed"
        raise RuntimeError(message)
    return result.stdout
