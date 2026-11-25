"""Check the assignment's Python size, naming and comparison rules."""

import ast
import re
from pathlib import Path

MAX_LINE_LENGTH = 80
MAX_FILE_LINES = 1000
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7
MAX_COMPLEXITY = 10
ALLOWED_COMPARISON_NUMBERS = (0, 1)
FUNCTION_NAME = re.compile(r"^_?[a-z][a-z0-9_]*$|^__[a-z]+__$")
ROOT = Path(__file__).resolve().parents[1]


def check_function(node: ast.FunctionDef, path: Path) -> list[str]:
    """Check one function against the limits listed in the assignment."""
    errors = []
    prefix = f"{path}:{node.lineno}: {node.name}"
    if node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES:
        errors.append(prefix + " exceeds the function line limit")
    arguments = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    if len(arguments) > MAX_ARGUMENTS:
        errors.append(prefix + " has too many arguments")
    if not FUNCTION_NAME.fullmatch(node.name):
        errors.append(prefix + " does not use snake_case")
    if ast.get_docstring(node) is None:
        errors.append(prefix + " has no docstring")
    branches = (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp)
    complexity = 1 + sum(isinstance(n, branches) for n in ast.walk(node))
    complexity += sum(
        len(n.values) - 1 for n in ast.walk(node) if isinstance(n, ast.BoolOp)
    )
    if complexity > MAX_COMPLEXITY:
        errors.append(prefix + " exceeds the complexity limit")
    return errors


def check_comparison(node: ast.Compare, path: Path) -> list[str]:
    """Find numeric comparison operands that need a named constant."""
    errors = []
    for value in [node.left, *node.comparators]:
        if not isinstance(value, ast.Constant):
            continue
        if isinstance(value.value, (int, float)):
            if value.value not in ALLOWED_COMPARISON_NUMBERS:
                errors.append(f"{path}:{node.lineno}: magic comparison")
    return errors


def check_source(path: Path) -> list[str]:
    """Inspect syntax, line length, functions and comparison constants."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    errors = []
    if len(lines) > MAX_FILE_LINES:
        errors.append(f"{path}: too many lines")
    for index, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_LENGTH:
            errors.append(f"{path}:{index}: line longer than 80 characters")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef):
            errors.extend(check_function(node, path))
        if isinstance(node, ast.Compare):
            errors.extend(check_comparison(node, path))
    return errors


def main() -> int:
    """Check tracked source directories without installing a linter."""
    errors = []
    paths = []
    for directory in ("src", "tests", "scripts"):
        paths.extend((ROOT / directory).rglob("*.py"))
    for path in sorted(paths):
        errors.extend(check_source(path))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Style checks passed: {len(paths)} Python files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
