"""Error parsing from test output."""

import re
from pathlib import Path
from typing import Optional, List

from deburger.models.error import ErrorInfo, TracebackFrame


class ErrorParser:
    """Parse Python tracebacks from test output."""

    # Pattern for standard Python traceback
    TRACEBACK_PATTERN = re.compile(
        r'File "(.+?)", line (\d+), in (.+?)\n\s+(.+?)(?=\n|$)',
        re.MULTILINE
    )

    # Pattern for error type and message
    ERROR_PATTERN = re.compile(
        r'^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*Error|Exception|Warning): (.+?)$',
        re.MULTILINE
    )

    def parse(self, output: str) -> Optional[ErrorInfo]:
        """
        Parse test output into structured error info.

        Args:
            output: Raw test output containing traceback

        Returns:
            ErrorInfo if parsing succeeds, None otherwise
        """
        # Extract all traceback frames
        frames = self._extract_frames(output)
        if not frames:
            return None

        # Get error type and message
        error_match = self.ERROR_PATTERN.search(output)
        if not error_match:
            return None

        error_type = error_match.group(1)
        message = error_match.group(2).strip()

        # Last frame is where error occurred
        last_frame = frames[-1]

        # Extract code context around error
        code_context = self._extract_code_context(
            last_frame.file_path,
            last_frame.line_number
        )

        return ErrorInfo(
            error_type=error_type,
            message=message,
            file_path=last_frame.file_path,
            line_number=last_frame.line_number,
            function_name=last_frame.function_name,
            traceback=frames,
            code_context=code_context,
        )

    def _extract_frames(self, output: str) -> List[TracebackFrame]:
        """Extract all traceback frames from output."""
        frames = []

        for match in self.TRACEBACK_PATTERN.finditer(output):
            file_path = match.group(1)
            line_number = int(match.group(2))
            function_name = match.group(3)
            code_line = match.group(4).strip()

            frames.append(TracebackFrame(
                file_path=file_path,
                line_number=line_number,
                function_name=function_name,
                code_line=code_line
            ))

        return frames

    def _extract_code_context(self, file_path: str, line_number: int, context_lines: int = 5) -> str:
        """
        Extract code context around error line.

        Args:
            file_path: Path to source file
            line_number: Line number where error occurred
            context_lines: Number of lines before/after to include

        Returns:
            Code snippet with context
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return ""

            with open(path) as f:
                lines = f.readlines()

            # Calculate range
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            # Build context with line numbers
            context_lines_list = []
            for i in range(start, end):
                line_num = i + 1
                marker = ">>>" if line_num == line_number else "   "
                context_lines_list.append(f"{marker} {line_num:4d} | {lines[i].rstrip()}")

            return "\n".join(context_lines_list)

        except Exception:
            return ""

    def parse_multiple(self, output: str) -> List[ErrorInfo]:
        """
        Parse multiple errors from test output.

        Args:
            output: Raw test output that may contain multiple failures

        Returns:
            List of ErrorInfo objects
        """
        errors = []

        # Split by common test failure markers
        failure_sections = re.split(
            r'(?:FAILED|ERROR|_+ test session fails _+)',
            output
        )

        for section in failure_sections:
            if not section.strip():
                continue

            error = self.parse(section)
            if error:
                errors.append(error)

        return errors
