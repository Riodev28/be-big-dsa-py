"""Small AST helpers shared by the time and space cost engines."""

from __future__ import annotations

import ast


def collect_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Top-level function/method definitions (methods of top-level classes too)."""
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)
        elif isinstance(node, ast.ClassDef):
            functions.extend(
                item
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    return functions


def looks_like_halving(node: ast.stmt) -> bool:
    """Heuristic: the statement (usually a while loop) divides something in half."""
    source = ast.unparse(node)
    return "// 2" in source or ">> 1" in source
