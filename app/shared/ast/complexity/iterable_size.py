"""Describe what a ``for`` loop iterates over: which Big-O variable it
introduces (or ``None`` for a constant-bounded loop) and whether it carries an
extra one-off cost such as ``for x in sorted(items)``."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IterSize:
    key: str | None  # None => constant-bounded loop (contributes no factor)
    sorts: bool = False  # iterable is sorted() => O(k log k) one-off cost


# Calls that return something the same size as their first argument.
_PASS_THROUGH = {"enumerate", "reversed", "list", "tuple", "iter"}
_VIEW_METHODS = {"items", "keys", "values"}


def describe_iter(node: ast.expr) -> IterSize:
    """Classify a ``for`` loop's iterable expression."""
    if isinstance(node, ast.Call):
        return _describe_call(node)

    constant_shapes = (
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        ast.Constant,
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
    )
    if isinstance(node, constant_shapes):
        return IterSize(None)

    return IterSize(_source_key(node))


def _describe_call(node: ast.Call) -> IterSize:
    name = callable_name(node)

    if name == "range":
        return _describe_range(node)

    if name == "sorted" and node.args:
        inner = describe_iter(node.args[0])
        return IterSize(inner.key, sorts=inner.key is not None)

    if name == "zip" and node.args:
        return describe_iter(node.args[0])

    if name in _PASS_THROUGH and node.args:
        return describe_iter(node.args[0])

    if isinstance(node.func, ast.Attribute) and node.func.attr in _VIEW_METHODS:
        return IterSize(_source_key(node.func.value))

    return IterSize(_source_key(node))


def _describe_range(node: ast.Call) -> IterSize:
    if not node.args:
        return IterSize(None)
    # range(stop) or range(start, stop[, step]); the growing bound is `stop`.
    bound = node.args[1] if len(node.args) >= 2 else node.args[0]
    return _describe_bound(bound)


def _describe_bound(node: ast.expr) -> IterSize:
    if isinstance(node, ast.Constant):
        return IterSize(None)
    if isinstance(node, ast.Call) and callable_name(node) == "len" and node.args:
        return IterSize(f"len({_source_key(node.args[0])})")
    if isinstance(node, ast.Name):
        return IterSize(node.id)
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult)
    ):
        for side in (node.right, node.left):
            described = _describe_bound(side)
            if described.key is not None:
                return described
        return IterSize(None)
    return IterSize(_source_key(node))


def callable_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _source_key(node: ast.expr) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - unparse is total on valid trees
        return node.__class__.__name__
