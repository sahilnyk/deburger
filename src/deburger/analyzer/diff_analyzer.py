"""Analyze code changes from git diffs."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CodeChange:
    file_path: str
    lines_added: int
    lines_removed: int
    hunks: list[tuple[int, int, str]]
    language: str


class DiffAnalyzer:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

    def get_changes(self, since: str = "HEAD~1") -> list[CodeChange]:
        result = subprocess.run(
            ["git", "diff", since, "--numstat"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        changes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            added, removed, filepath = line.split(maxsplit=2)
            if added == "-" or removed == "-":
                continue

            changes.append(
                CodeChange(
                    file_path=filepath,
                    lines_added=int(added),
                    lines_removed=int(removed),
                    hunks=[],
                    language=self._detect_language(filepath),
                )
            )

        return changes

    def _detect_language(self, filepath: str) -> str:
        ext = Path(filepath).suffix
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        return lang_map.get(ext, "unknown")

    def get_file_content(self, filepath: str, ref: str = "HEAD") -> str:
        result = subprocess.run(
            ["git", "show", f"{ref}:{filepath}"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
