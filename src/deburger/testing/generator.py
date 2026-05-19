"""Generate tests from code analysis."""

import ast
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeneratedTest:
    name: str
    code: str
    test_type: str
    description: str


class TestGenerator:
    def generate_for_function(self, func_name: str, func_code: str) -> list[GeneratedTest]:
        try:
            tree = ast.parse(func_code)
        except SyntaxError:
            return []

        tests = []
        func_node = self._find_function(tree, func_name)

        if not func_node:
            return []

        tests.append(self._generate_happy_path(func_node))
        tests.extend(self._generate_edge_cases(func_node))
        tests.append(self._generate_error_case(func_node))

        return tests

    def _find_function(self, tree: ast.AST, func_name: str) -> Optional[ast.FunctionDef]:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node
        return None

    def _generate_happy_path(self, func: ast.FunctionDef) -> GeneratedTest:
        args = [arg.arg for arg in func.args.args if arg.arg != "self"]
        args_str = ", ".join(args)
        test_args = ", ".join(f"mock_{arg}" for arg in args)

        code = f"""def test_{func.name}_success():
    result = {func.name}({test_args})
    assert result is not None
"""

        return GeneratedTest(
            name=f"test_{func.name}_success",
            code=code,
            test_type="unit",
            description=f"Happy path test for {func.name}",
        )

    def _generate_edge_cases(self, func: ast.FunctionDef) -> list[GeneratedTest]:
        tests = []
        args = [arg.arg for arg in func.args.args if arg.arg != "self"]

        if args:
            code = f"""def test_{func.name}_empty_input():
    result = {func.name}(None)
    assert result is not None
"""
            tests.append(
                GeneratedTest(
                    name=f"test_{func.name}_empty_input",
                    code=code,
                    test_type="unit",
                    description=f"Test {func.name} with None input",
                )
            )

        return tests

    def _generate_error_case(self, func: ast.FunctionDef) -> GeneratedTest:
        code = f"""def test_{func.name}_error_handling():
    with pytest.raises(Exception):
        {func.name}(invalid_input)
"""

        return GeneratedTest(
            name=f"test_{func.name}_error_handling",
            code=code,
            test_type="unit",
            description=f"Error handling test for {func.name}",
        )

    def generate_integration_test(self, module_name: str) -> GeneratedTest:
        code = f"""def test_{module_name}_integration():
    result = run_full_workflow()
    assert result.success is True
    assert result.errors == []
"""

        return GeneratedTest(
            name=f"test_{module_name}_integration",
            code=code,
            test_type="integration",
            description=f"Integration test for {module_name}",
        )
