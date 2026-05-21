"""Fast parallel code scanner - analyzes entire codebase quickly."""

import asyncio
from pathlib import Path
from typing import List, Dict, Set
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from deburger.analyzers.base import Issue
from deburger.analyzers.registry import AnalyzerRegistry


@dataclass
class ScanResult:
    """Results from scanning a file."""
    file_path: str
    issues: List[Issue]
    scan_time_ms: float
    error: str = None


class FastScanner:
    """Parallel code scanner that's actually fast."""

    def __init__(self, config: dict, max_workers: int = None):
        self.config = config
        self.max_workers = max_workers or min(32, (asyncio.cpu_count() or 1) * 4)
        self.file_cache = {}

    async def scan_path(self, path: str, incremental: bool = True) -> List[Issue]:
        """
        Scan path for issues (parallel and fast).

        Args:
            path: Directory or file to scan
            incremental: Only scan changed files (git diff)
        """
        files = await self._get_files_to_scan(path, incremental)

        if not files:
            return []

        # Scan all files in parallel using process pool
        scan_results = await self._scan_files_parallel(files)

        # Flatten issues from all files
        all_issues = []
        for result in scan_results:
            if result.error:
                continue
            all_issues.extend(result.issues)

        return all_issues

    async def _get_files_to_scan(self, path: str, incremental: bool) -> List[Path]:
        """Get list of files to scan."""
        path_obj = Path(path)

        if path_obj.is_file():
            return [path_obj]

        # Find all supported files
        extensions = self._get_supported_extensions()
        files = []

        for ext in extensions:
            files.extend(path_obj.rglob(f"*{ext}"))

        # If incremental, only scan changed files
        if incremental:
            files = await self._filter_changed_files(files)

        return files

    def _get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions."""
        extensions = set()
        for analyzer_name in AnalyzerRegistry.list_analyzers():
            analyzer = AnalyzerRegistry.get(analyzer_name)
            extensions.update(analyzer.supported_languages)
        return extensions

    async def _filter_changed_files(self, files: List[Path]) -> List[Path]:
        """Filter to only changed files (git diff)."""
        import subprocess

        try:
            # Get changed files from git
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return files

            changed = set(result.stdout.strip().split("\n"))

            # Also check staged files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                changed.update(result.stdout.strip().split("\n"))

            # Filter files
            return [f for f in files if str(f) in changed]

        except Exception:
            # If git fails, scan everything
            return files

    async def _scan_files_parallel(self, files: List[Path]) -> List[ScanResult]:
        """Scan files in parallel using process pool."""
        loop = asyncio.get_event_loop()

        # Use process pool for CPU-bound AST parsing
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self._scan_file_sync,
                    str(file_path)
                )
                for file_path in files
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        return [r for r in results if isinstance(r, ScanResult)]

    def _scan_file_sync(self, file_path: str) -> ScanResult:
        """Scan single file (runs in process pool)."""
        import time
        start = time.time()

        try:
            # Get appropriate analyzer
            analyzer = AnalyzerRegistry.get_for_file(file_path)
            if not analyzer:
                return ScanResult(file_path, [], 0)

            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Analyze
            issues = analyzer.analyze(file_path, code, self.config)

            elapsed_ms = (time.time() - start) * 1000

            return ScanResult(file_path, issues, elapsed_ms)

        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            return ScanResult(file_path, [], elapsed_ms, error=str(e))

    async def scan_with_progress(self, path: str, callback=None) -> List[Issue]:
        """Scan with progress callback."""
        files = await self._get_files_to_scan(path, incremental=False)
        total = len(files)

        if callback:
            callback(0, total)

        results = []
        completed = 0

        # Process in batches for progress updates
        batch_size = max(10, total // 10)

        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_results = await self._scan_files_parallel(batch)

            for result in batch_results:
                if not result.error:
                    results.extend(result.issues)

            completed += len(batch)
            if callback:
                callback(completed, total)

        return results
