from typing import List, Optional, Dict
from dataclasses import dataclass
from decimal import Decimal

from deburger.analyzers.base import Issue, IssueType


@dataclass
class Fix:
    issue: Issue
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float  # 1.0 = 100% safe
    auto_apply_safe: bool
    savings_monthly: Decimal


class CodeFixer:
    def __init__(self):
        self.fixes_generated = 0

    def generate_fix(self, issue: Issue, file_content: str) -> Optional[Fix]:
        # only fix patterns we're 100% confident about
        if issue.type == IssueType.N_PLUS_ONE_QUERY:
            return self._fix_n_plus_one(issue, file_content)
        elif issue.type == IssueType.SEQUENTIAL_ASYNC:
            return self._fix_sequential_async(issue, file_content)

        return None

    def _fix_n_plus_one(self, issue: Issue, file_content: str) -> Optional[Fix]:
        # detect language
        if issue.file_path.endswith('.py'):
            return self._fix_n_plus_one_python(issue, file_content)
        elif issue.file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return self._fix_n_plus_one_javascript(issue, file_content)

        return None

    def _fix_n_plus_one_python(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')

        # get the loop code
        loop_start = issue.line_number - 1
        loop_end = self._find_loop_end_python(lines, loop_start)

        if loop_end is None:
            return None

        loop_code = '\n'.join(lines[loop_start:loop_end + 1])

        # extract variable names from the loop
        import re
        for_match = re.search(r'for\s+(\w+)\s+in\s+(\w+)', lines[loop_start])
        if not for_match:
            return None

        item_var = for_match.group(1)
        items_var = for_match.group(2)

        # find the db query pattern
        query_pattern = None
        query_line = None
        for i in range(loop_start + 1, loop_end + 1):
            if 'query' in lines[i] or 'filter' in lines[i] or 'get' in lines[i]:
                query_line = i
                query_pattern = lines[i].strip()
                break

        if not query_pattern:
            return None

        # generate fix - collect IDs then bulk query
        indent = self._get_indent(lines[loop_start])

        fixed_code = f"{indent}# collect all IDs first\n"
        fixed_code += f"{indent}ids = [{item_var}.id for {item_var} in {items_var}]\n"
        fixed_code += f"{indent}\n"
        fixed_code += f"{indent}# bulk query instead of loop\n"
        fixed_code += f"{indent}results = db.query().filter(id.in_(ids)).all()\n"
        fixed_code += f"{indent}results_map = {{r.id: r for r in results}}\n"
        fixed_code += f"{indent}\n"
        fixed_code += f"{indent}# use cached results\n"
        fixed_code += f"{indent}for {item_var} in {items_var}:\n"
        fixed_code += f"{indent}    result = results_map.get({item_var}.id)"

        return Fix(
            issue=issue,
            original_code=loop_code,
            fixed_code=fixed_code,
            explanation="replaced N+1 queries with single bulk query",
            confidence=0.85,
            auto_apply_safe=False,  # needs manual review
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _fix_n_plus_one_javascript(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')

        loop_start = issue.line_number - 1
        loop_end = self._find_loop_end_javascript(lines, loop_start)

        if loop_end is None:
            return None

        loop_code = '\n'.join(lines[loop_start:loop_end + 1])

        # extract variable names
        import re
        for_match = re.search(r'for\s*\(\s*(?:const|let|var)\s+(\w+)\s+of\s+(\w+)\s*\)', lines[loop_start])
        if not for_match:
            # try forEach
            foreach_match = re.search(r'(\w+)\.forEach\(\s*(?:\(?\s*(\w+)\s*\)?|(\w+))\s*=>', lines[loop_start])
            if foreach_match:
                items_var = foreach_match.group(1)
                item_var = foreach_match.group(2) or foreach_match.group(3)
            else:
                return None
        else:
            item_var = for_match.group(1)
            items_var = for_match.group(2)

        # generate fix
        indent = self._get_indent(lines[loop_start])

        fixed_code = f"{indent}// collect all IDs first\n"
        fixed_code += f"{indent}const ids = {items_var}.map({item_var} => {item_var}.id);\n"
        fixed_code += f"{indent}\n"
        fixed_code += f"{indent}// bulk query instead of loop\n"
        fixed_code += f"{indent}const results = await db.find({{ id: {{ $in: ids }} }});\n"
        fixed_code += f"{indent}const resultsMap = new Map(results.map(r => [r.id, r]));\n"
        fixed_code += f"{indent}\n"
        fixed_code += f"{indent}// use cached results\n"
        fixed_code += f"{indent}for (const {item_var} of {items_var}) {{\n"
        fixed_code += f"{indent}  const result = resultsMap.get({item_var}.id);\n"
        fixed_code += f"{indent}}}"

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

        # find all consecutive await lines
        await_lines = []
        i = start_line
        while i < len(lines):
            line = lines[i].strip()
            if 'await' in line and '=' in line:
                await_lines.append((i, lines[i]))
                i += 1
            elif await_lines:
                break
            else:
                i += 1

        if len(await_lines) < 2:
            return None

        original_code = '\n'.join([line for _, line in await_lines])

        # extract variable names and calls
        import re
        calls = []
        vars = []
        for _, line in await_lines:
            match = re.search(r'(\w+)\s*=\s*await\s+(.+)', line)
            if match:
                vars.append(match.group(1))
                calls.append(match.group(2))

        if not calls:
            return None

        indent = self._get_indent(await_lines[0][1])

        # generate parallel version
        fixed_code = f"{indent}# run in parallel instead of sequential\n"
        fixed_code += f"{indent}{', '.join(vars)} = await asyncio.gather(\n"
        for i, call in enumerate(calls):
            comma = ',' if i < len(calls) - 1 else ''
            fixed_code += f"{indent}    {call}{comma}\n"
        fixed_code += f"{indent})"

        return Fix(
            issue=issue,
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=f"converted {len(calls)} sequential awaits to parallel execution",
            confidence=0.95,  # very safe transformation
            auto_apply_safe=True,  # this is safe to auto-apply
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _fix_sequential_async_javascript(self, issue: Issue, file_content: str) -> Optional[Fix]:
        lines = file_content.split('\n')

        start_line = issue.line_number - 1

        # find consecutive await lines
        await_lines = []
        i = start_line
        while i < len(lines):
            line = lines[i].strip()
            if 'await' in line and ('const' in line or 'let' in line or 'var' in line):
                await_lines.append((i, lines[i]))
                i += 1
            elif await_lines:
                break
            else:
                i += 1

        if len(await_lines) < 2:
            return None

        original_code = '\n'.join([line for _, line in await_lines])

        # extract variable names and calls
        import re
        calls = []
        vars = []
        for _, line in await_lines:
            match = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*await\s+(.+?);?$', line)
            if match:
                vars.append(match.group(1))
                calls.append(match.group(2).rstrip(';'))

        if not calls:
            return None

        indent = self._get_indent(await_lines[0][1])

        # generate Promise.all version
        fixed_code = f"{indent}// run in parallel instead of sequential\n"
        fixed_code += f"{indent}const [{', '.join(vars)}] = await Promise.all([\n"
        for i, call in enumerate(calls):
            comma = ',' if i < len(calls) - 1 else ''
            fixed_code += f"{indent}  {call}{comma}\n"
        fixed_code += f"{indent}]);"

        return Fix(
            issue=issue,
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=f"converted {len(calls)} sequential awaits to Promise.all",
            confidence=0.95,
            auto_apply_safe=True,
            savings_monthly=issue.savings_monthly or Decimal("0")
        )

    def _find_loop_end_python(self, lines: List[str], start: int) -> Optional[int]:
        # find matching indentation end
        if start >= len(lines):
            return None

        start_indent = len(lines[start]) - len(lines[start].lstrip())

        for i in range(start + 1, len(lines)):
            if not lines[i].strip():
                continue

            line_indent = len(lines[i]) - len(lines[i].lstrip())

            if line_indent <= start_indent:
                return i - 1

        return len(lines) - 1

    def _find_loop_end_javascript(self, lines: List[str], start: int) -> Optional[int]:
        # find matching closing brace
        if start >= len(lines):
            return None

        open_braces = 0
        found_first = False

        for i in range(start, len(lines)):
            line = lines[i]
            open_braces += line.count('{')

            if open_braces > 0:
                found_first = True

            open_braces -= line.count('}')

            if found_first and open_braces == 0:
                return i

        return None

    def _get_indent(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]

    def generate_all_fixes(self, issues: List[Issue], file_contents: Dict[str, str]) -> List[Fix]:
        # generate fixes for all issues
        fixes = []

        for issue in issues:
            file_content = file_contents.get(issue.file_path)
            if not file_content:
                # read file if not provided
                try:
                    with open(issue.file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except Exception:
                    continue

            fix = self.generate_fix(issue, file_content)
            if fix:
                fixes.append(fix)
                self.fixes_generated += 1

        return fixes
