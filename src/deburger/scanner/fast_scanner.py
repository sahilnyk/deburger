import os
import asyncio
import subprocess
import time
from pathlib import Path
from typing import List, Set
from dataclasses import dataclass

from deburger.analyzers.base import Issue
from deburger.analyzers.registry import AnalyzerRegistry


@dataclass
class ScanResult:
    file_path: str
    issues: List[Issue]
    scan_time_ms: float
    error: str = None


class FastScanner:
    def __init__(self, config: dict, max_workers: int = None):
        self.config = config
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 4)
        self.errors: List[ScanResult] = []

    async def scan_path(self, path: str, incremental: bool = True) -> List[Issue]:
        # get files to scan (changed files if incremental)
        files = await self._get_files_to_scan(path, incremental)

        if not files:
            return []

        # scan everything in parallel
        scan_results = await self._scan_files_parallel(files)
        self.errors = [result for result in scan_results if result.error]

        # collect all issues
        all_issues = []
        for result in scan_results:
            if result.error:
                continue
            all_issues.extend(result.issues)

        return all_issues

    async def _get_files_to_scan(self, path: str, incremental: bool) -> List[Path]:
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"scan path does not exist: {path}")

        if path_obj.is_file():
            return [path_obj]

        # find all supported files
        extensions = self._get_supported_extensions()
        files = []

        for ext in extensions:
            files.extend(path_obj.rglob(f"*{ext}"))

        # filter out ignored paths
        ignore_patterns = self.config.get("ignore", [
            "node_modules", "venv", ".venv", "__pycache__",
            "test_", "_test.py", ".test.", "spec.",
            "site-packages", "deburger/analyzers/patterns",
        ])
        files = [f for f in files if not any(ig in str(f) for ig in ignore_patterns)]

        # only scan changed files if incremental
        if incremental:
            files = await self._filter_changed_files(files)

        return files

    def _get_supported_extensions(self) -> Set[str]:
        extensions = set()
        for analyzer_name in AnalyzerRegistry.list_analyzers():
            analyzer = AnalyzerRegistry.get(analyzer_name)
            extensions.update(analyzer.supported_languages)
        return extensions

    async def _filter_changed_files(self, files: List[Path]) -> List[Path]:
        try:
            # get changed files from git (unstaged)
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return files

            changed = set(result.stdout.strip().split("\n"))

            # also check staged files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                changed.update(result.stdout.strip().split("\n"))

            # also check untracked files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                changed.update(result.stdout.strip().split("\n"))

            # resolve changed paths to absolute for comparison
            changed_resolved = set()
            for c in changed:
                if c:
                    changed_resolved.add(Path(c).resolve())

            return [f for f in files if f.resolve() in changed_resolved]

        except Exception:
            # git failed, scan everything
            return files

    async def _scan_files_parallel(self, files: List[Path]) -> List[ScanResult]:
        results = []
        for index, file_path in enumerate(files):
            results.append(self._scan_file_sync(str(file_path)))
            if index % 50 == 49:
                await asyncio.sleep(0)
        return results

    def _scan_file_sync(self, file_path: str) -> ScanResult:
        start = time.time()

        try:
            analyzer = AnalyzerRegistry.get_for_file(file_path)
            if not analyzer:
                return ScanResult(file_path, [], 0)

            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            issues = analyzer.analyze(file_path, code, self.config)
            elapsed_ms = (time.time() - start) * 1000

            return ScanResult(file_path, issues, elapsed_ms)

        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            return ScanResult(file_path, [], elapsed_ms, error=str(e))
