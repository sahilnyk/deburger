"""Structured logging system for deburger."""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler


class DeburgerLogger:
    """Centralized logging with file rotation and structured output."""

    def __init__(self, name: str = "deburger"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = Path.home() / ".deburger" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing handlers
        self.logger.handlers = []

        # File handler with rotation (10MB max, keep 5 backups)
        log_file = self.log_dir / "deburger.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler (only warnings and errors)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Structured JSON log file
        self.json_log_file = self.log_dir / "deburger.jsonl"

    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured data as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        with open(self.json_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message)
        self._log_structured("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message)
        self._log_structured("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message)
        self._log_structured("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message)
        self._log_structured("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message)
        self._log_structured("CRITICAL", message, **kwargs)

    def log_command(self, command: str, **kwargs):
        """Log CLI command execution."""
        self.info(f"Command executed: {command}", command=command, **kwargs)

    def log_analysis(self, files: int, lines_added: int, lines_removed: int, **kwargs):
        """Log analysis results."""
        self.info(
            f"Analysis completed: {files} files, +{lines_added}/-{lines_removed}",
            files=files,
            lines_added=lines_added,
            lines_removed=lines_removed,
            **kwargs,
        )

    def log_security_issue(self, issue_type: str, severity: str, file_path: str, line: int):
        """Log security vulnerability found."""
        self.warning(
            f"Security issue: {issue_type} ({severity}) in {file_path}:{line}",
            issue_type=issue_type,
            severity=severity,
            file=file_path,
            line=line,
        )

    def get_recent_logs(self, lines: int = 50) -> list[str]:
        """Get recent log lines."""
        log_file = self.log_dir / "deburger.log"
        if not log_file.exists():
            return []

        with open(log_file, "r") as f:
            all_lines = f.readlines()
            return all_lines[-lines:]

    def clear_logs(self):
        """Clear all log files."""
        for log_file in self.log_dir.glob("*.log*"):
            log_file.unlink(missing_ok=True)
        self.json_log_file.unlink(missing_ok=True)
        self.info("Logs cleared")


# Global logger instance
logger = DeburgerLogger()


def get_logger(name: str = "deburger") -> DeburgerLogger:
    """Get logger instance."""
    return logger
