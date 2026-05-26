#!/usr/bin/env python3
"""Valida restricciones de builtins en archivos Python de performance_evaluations."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_NAMES = frozenset({"print", "ValueError"})

ALLOWED_DIRECT_CALLS = frozenset(
    {
        "__build_class__",
        "__import__",
        "abs",
        "any",
        "bool",
        "defaultdict",
        "dict",
        "float",
        "id",
        "int",
        "isinstance",
        "len",
        "list",
        "max",
        "min",
        "object",
        "range",
        "round",
        "set",
        "str",
        "sum",
        "tuple",
    }
)

SKIP_FILES = frozenset({"validate_restricted_builtins.py"})


def _line(node: ast.AST, source: list[str]) -> str:
    lineno = getattr(node, "lineno", None)
    if lineno is None or lineno < 1 or lineno > len(source):
        return ""
    return source[lineno - 1].strip()


def validate_source(source: str, path: str = "<string>") -> list[str]:
    lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [f"{path}:{exc.lineno}: error de sintaxis: {exc.msg}"]

    errors: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            errors.append(
                f"{path}:{node.lineno}: nombre prohibido '{node.id}': {_line(node, lines)}"
            )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in FORBIDDEN_NAMES:
                errors.append(
                    f"{path}:{node.lineno}: llamada prohibida '{name}()': {_line(node, lines)}"
                )
            elif name not in ALLOWED_DIRECT_CALLS:
                errors.append(
                    f"{path}:{node.lineno}: llamada directa no permitida '{name}()'. "
                    f"Permitidas: {', '.join(sorted(ALLOWED_DIRECT_CALLS))}"
                )

    return errors


def validate_file(file_path: Path) -> list[str]:
    if file_path.name in SKIP_FILES:
        return []
    return validate_source(file_path.read_text(encoding="utf-8"), str(file_path))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "Uso: python performance_evaluations/validate_restricted_builtins.py <archivo.py> [...]",
            file=sys.stderr,
        )
        return 2

    has_errors = False
    for raw in args:
        path = Path(raw)
        if not path.is_file():
            print(f"Archivo no encontrado: {path}", file=sys.stderr)
            has_errors = True
            continue
        for err in validate_file(path):
            print(err, file=sys.stderr)
            has_errors = True

    if has_errors:
        return 1
    print("OK: cumple restricciones de funciones permitidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
