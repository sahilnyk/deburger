import re
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from decimal import Decimal

from deburger.analyzers.base import Issue, IssueType
from deburger.optimizer.cache import FileCache

_PY_FOR_RE = re.compile(r'for\s+(\w+)\s+in\s+(\w+)')
_JS_FOR_OF_RE = re.compile(r'for\s*\(\s*(?:const|let|var)\s+(\w+)\s+of\s+(\w+)\s*\)')
_JS_FOREACH_RE = re.compile(r'(\w+)\.forEach\(\s*(?:\(?\s*(\w+)\s*\)?|(\w+))\s*=>')
_PY_AWAIT_RE = re.compile(r'(\w+)\s*=\s*await\s+(.+)')
_JS_AWAIT_RE = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*await\s+(.+?);?$')


@dataclass
class Fix:
    issue: Issue
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float
    auto_apply_safe: bool
    savings_monthly: Decimal


class CodeFixer:
    def __init__(self):
        self.fixes_generated = 0
        self.file_cache = FileCache()

    def generate_fix(self, issue: Issue, file_content: str) -> Optional[Fix]:
        if issue.type == IssueType.N_PLUS_ONE_QUERY:
            return self._fix_n_plus_one(issue, file_content)
        elif issue.type == IssueType.SEQUENTIAL_ASYNC:
            return self._fix_sequential_async(issue, file_content)
        return None

    def _fix_n_plus_one(self, issue: Issue, file_content: str) -> Optional[Fix]:
        if issue.file_path.endswith('.py'):
            return self._fix_n_plus_one_python(issue, file_content)
        elif issue.file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return self._fix_n_plus_one_javascript(issue, file_content)
        return None

    def _fix_n_plus_one_python(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')
        loop_start = issue.line_number - 1
        loop_end = self._find_loop_end_python(lines, loop_start)

        if loop_end is None:
            return None

        loop_code = '\n'.join(lines[loop_start:loop_end + 1])

        for_match = _PY_FOR_RE.search(lines[loop_start])
        if not for_match:
            return None

        item_var = for_match.group(1)
        items_var = for_match.group(2)
        indent = self._get_indent(lines[loop_start])

        fixed_code = (
            f"{indent}ids = [{item_var}.id for {item_var} in {items_var}]\n"
            f"{indent}results = db.query().filter(id.in_(ids)).all()\n"
            f"{indent}results_map = {{r.id: r for r in results}}\n"
            f"{indent}\n"
            f"{indent}for {item_var} in {items_var}:\n"
            f"{indent}    result = results_map.get({item_var}.id)"
        )

        return Fix(
            issue=issue,
            original_code=loop_code,
            fixed_code=fixed_code,
            explanation="replaced N+1 queries with single bulk query",
            confidence=0.85,
            auto_apply_safe=False,
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _fix_n_plus_one_javascript(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')
        loop_start = issue.line_number - 1
        loop_end = self._find_loop_end_javascript(lines, loop_start)

        if loop_end is None:
            return None

        loop_code = '\n'.join(lines[loop_start:loop_end + 1])

        for_match = _JS_FOR_OF_RE.search(lines[loop_start])
        if for_match:
            item_var = for_match.group(1)
            items_var = for_match.group(2)
        else:
            foreach_match = _JS_FOREACH_RE.search(lines[loop_start])
            if foreach_match:
                items_var = foreach_match.group(1)
                item_var = foreach_match.group(2) or foreach_match.group(3)
            else:
                return None

        indent = self._get_indent(lines[loop_start])

        fixed_code = (
            f"{indent}const ids = {items_var}.map({item_var} => {item_var}.id);\n"
            f"{indent}const results = await db.find({{ id: {{ $in: ids }} }});\n"
            f"{indent}const resultsMap = new Map(results.map(r => [r.id, r]));\n"
            f"{indent}\n"
            f"{indent}for (const {item_var} of {items_var}) {{\n"
            f"{indent}  const result = resultsMap.get({item_var}.id);\n"
            f"{indent}}}"
        )

        return Fix(
            issue=issue,
            original_code=loop_code,
            fixed_code=fixed_code,
            explanation="replaced N+1 queries with single bulk query",
            confidence=0.85,
            auto_apply_safe=False,
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _fix_sequential_async(self, issue: Issue, file_content: str) -> Optional[Fix]:
        if issue.file_path.endswith('.py'):
            return self._fix_sequential_async_python(issue, file_content)
        elif issue.file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return self._fix_sequential_async_javascript(issue, file_content)
        return None

    def _fix_sequential_async_python(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')
        start_line = issue.line_number - 1

        search_window = lines[start_line:min(start_line + 50, len(lines))]
        await_lines = []

        for i, line in enumerate(search_window):
            if 'await' in line and '=' in line:
                await_lines.append((start_line + i, line))
            elif await_lines:
                break

        if len(await_lines) < 2:
            return None

        original_code = '\n'.join(line for _, line in await_lines)

        matches = [_PY_AWAIT_RE.search(line) for _, line in await_lines]
        vars_list = [m.group(1) for m in matches if m]
        calls = [m.group(2) for m in matches if m]

        if not calls:
            return None

        indent = self._get_indent(await_lines[0][1])

        fixed_lines = [f"{indent}{', '.join(vars_list)} = await asyncio.gather("]
        for i, call in enumerate(calls):
            comma = ',' if i < len(calls) - 1 else ''
            fixed_lines.append(f"{indent}    {call}{comma}")
        fixed_lines.append(f"{indent})")

        return Fix(
            issue=issue,
            original_code=original_code,
            fixed_code='\n'.join(fixed_lines),
            explanation=f"converted {len(calls)} sequential awaits to parallel execution",
            confidence=0.95,
            auto_apply_safe=True,
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _fix_sequential_async_javascript(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')
        start_line = issue.line_number - 1

        search_window = lines[start_line:min(start_line + 50, len(lines))]
        await_lines = []

        for i, line in enumerate(search_window):
            if 'await' in line and any(kw in line for kw in ['const', 'let', 'var']):
                await_lines.append((start_line + i, line))
            elif await_lines:
                break

        if len(await_lines) < 2:
            return None

        original_code = '\n'.join(line for _, line in await_lines)

        matches = [_JS_AWAIT_RE.search(line) for _, line in await_lines]
        vars_list = [m.group(1) for m in matches if m]
        calls = [m.group(2).rstrip(';') for m in matches if m]

        if not calls:
            return None

        indent = self._get_indent(await_lines[0][1])

        fixed_lines = [f"{indent}const [{', '.join(vars_list)}] = await Promise.all(["]
        for i, call in enumerate(calls):
            comma = ',' if i < len(calls) - 1 else ''
            fixed_lines.append(f"{indent}  {call}{comma}")
        fixed_lines.append(f"{indent}]);")

        return Fix(
            issue=issue,
            original_code=original_code,
            fixed_code='\n'.join(fixed_lines),
            explanation=f"converted {len(calls)} sequential awaits to Promise.all",
            confidence=0.95,
            auto_apply_safe=True,
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _find_loop_end_python(self, lines: List[str], start: int) -> Optional[int]:
        if start >= len(lines):
            return None

        start_indent = len(lines[start]) - len(lines[start].lstrip())

        for i in range(start + 1, min(start + 100, len(lines))):
            if not lines[i].strip():
                continue
            if len(lines[i]) - len(lines[i].lstrip()) <= start_indent:
                return i - 1

        return min(start + 99, len(lines) - 1)

    def _find_loop_end_javascript(self, lines: List[str], start: int) -> Optional[int]:
        if start >= len(lines):
            return None

        open_braces = 0
        found_first = False

        for i in range(start, min(start + 100, len(lines))):
            open_braces += lines[i].count('{')
            if open_braces > 0:
                found_first = True
            open_braces -= lines[i].count('}')
            if found_first and open_braces == 0:
                return i

        return None

    def _get_indent(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]

    async def generate_all_fixes(self, issues: List[Issue], file_contents: Dict[str, str]) -> List[Fix]:
        loop = asyncio.get_event_loop()

        async def generate_one(issue):
            file_content = file_contents.get(issue.file_path)
            if not file_content:
                file_content = self.file_cache.get(issue.file_path)
            if not file_content:
                try:
                    with open(issue.file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except Exception:
                    return None

            fix = await loop.run_in_executor(None, self.generate_fix, issue, file_content)
            if fix:
                self.fixes_generated += 1
            return fix

        tasks = [generate_one(issue) for issue in issues]
        results = await asyncio.gather(*tasks)

        return [fix for fix in results if fix is not None]
