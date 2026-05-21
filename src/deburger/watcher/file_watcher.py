"""File system watcher for continuous monitoring."""

import time
from pathlib import Path
from typing import Callable, Set, Optional
from datetime import datetime, timedelta


class FileWatcher:
    """Watch directory for file changes and trigger scans."""

    def __init__(
        self,
        watch_path: str,
        callback: Callable[[str], None],
        interval: float = 2.0,
        ignore_patterns: Optional[list] = None,
    ):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.interval = interval
        self.ignore_patterns = ignore_patterns or [
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
        ]
        self.file_mtimes: dict = {}
        self.running = False

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def get_files_to_watch(self) -> Set[Path]:
        """Get all files to watch."""
        files = set()

        # Watch specific file extensions
        extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rb", ".php"]

        for ext in extensions:
            for file_path in self.watch_path.rglob(f"*{ext}"):
                if not self.should_ignore(file_path):
                    files.add(file_path)

        return files

    def initialize_mtimes(self):
        """Initialize modification times for all watched files."""
        self.file_mtimes = {}
        for file_path in self.get_files_to_watch():
            try:
                self.file_mtimes[file_path] = file_path.stat().st_mtime
            except OSError:
                pass

    def check_for_changes(self) -> Set[Path]:
        """Check for file changes and return changed files."""
        changed_files = set()
        current_files = self.get_files_to_watch()

        # Check for modified files
        for file_path in current_files:
            try:
                current_mtime = file_path.stat().st_mtime
                if file_path not in self.file_mtimes:
                    # New file
                    self.file_mtimes[file_path] = current_mtime
                    changed_files.add(file_path)
                elif current_mtime > self.file_mtimes[file_path]:
                    # Modified file
                    self.file_mtimes[file_path] = current_mtime
                    changed_files.add(file_path)
            except OSError:
                pass

        # Check for deleted files
        deleted_files = set(self.file_mtimes.keys()) - current_files
        for file_path in deleted_files:
            del self.file_mtimes[file_path]

        return changed_files

    def watch(self):
        """Start watching for file changes."""
        self.running = True
        self.initialize_mtimes()

        last_scan = datetime.now()
        scan_cooldown = timedelta(seconds=3)  # Don't scan more than once per 3 seconds

        try:
            while self.running:
                changed_files = self.check_for_changes()

                if changed_files:
                    now = datetime.now()
                    if now - last_scan > scan_cooldown:
                        # Trigger callback with watch path
                        self.callback(str(self.watch_path))
                        last_scan = now

                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching."""
        self.running = False
