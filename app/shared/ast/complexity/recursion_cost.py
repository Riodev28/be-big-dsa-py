"""Classify a self-recursive function into a Big-O class using recursion-tree
reasoning (a pragmatic subset of the Master Theorem).

Inputs the classifier looks at:

* ``branches`` - how many self-calls happen per invocation (``if``/``elif``
  branches are mutually exclusive -> ``max``; sequential calls -> sum).
* ``shrink`` - ``"halve"`` when the recursive argument is divided (``// 2``,
  ``>> 1``, half-slice), otherwise ``"subtract"``.
* ``work`` - the non-recursive body cost (self-calls treated as O(1)).
"""

from __future__ import annotations

import ast

from .expression import Complexity

_RECURSION_VARIABLE = "n"

# Ordering used to pick the "worst" recursion shape across several functions.
SPACE_KIND_RANK = {
    None: 0,
    "none": 0,
    "logarithmic": 1,
    "linear": 2,
    "divide_and_conquer": 2,
    "polynomial": 3,
}


def is_recursive(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return bool(_self_calls(func))


def classify(
    func: ast.FunctionDef | ast.AsyncFunctionDef, work: Complexity
) -> tuple[str, Complexity]:
    """Return ``(kind, complexity)`` for recursive *func* whose non-recursive
    body cost is *work*."""
    calls = _self_calls(func)
    if not calls:
        return ("none", work)

    branches = _effective_branches(func.body, func.name)
    shrink = _detect_shrink(func, calls)
    work_degree = work.max_degree()

    if branches <= 1:
        if shrink == "halve":
            if work_degree == 0:
                return ("logarithmic", Complexity.logarithmic())
            return ("linear", Complexity.linear(_RECURSION_VARIABLE))
        if work_degree == 0:
            return ("linear", Complexity.linear(_RECURSION_VARIABLE))
        return ("polynomial", Complexity.power(_RECURSION_VARIABLE, work_degree + 1))

    # two or more self-calls per invocation
    if shrink == "halve":
        if work_degree == 0:
            return ("divide_and_conquer", Complexity.linear(_RECURSION_VARIABLE))
        return (
            "divide_and_conquer",
            Complexity.linear(_RECURSION_VARIABLE).times_log(),
        )

    return ("exponential", Complexity.exponential())


def classify_space(
    func: ast.FunctionDef | ast.AsyncFunctionDef, per_frame: Complexity
) -> tuple[str, Complexity]:
    """Return ``(kind, complexity)`` for the *call-stack* space of a recursive
    function. Space depends on the recursion **depth**, not the number of calls,
    so tree recursion (fibonacci) is ``O(n)`` here, not ``O(2^n)``.

    *per_frame* is any non-constant allocation each frame holds onto (a slice,
    a copy, a concat) — it accumulates down the live call path.
    """
    calls = _self_calls(func)
    if not calls:
        return ("none", per_frame)

    shrink = _detect_shrink(func, calls)
    frame_degree = per_frame.max_degree()

    if shrink == "halve":
        depth = Complexity.logarithmic()
        # slices down one path form a geometric series -> O(n)
        held = (
            Complexity.linear(_RECURSION_VARIABLE)
            if frame_degree
            else Complexity.constant()
        )
        kind = "divide_and_conquer" if frame_degree else "logarithmic"
        return (kind, depth.add(held))

    depth = Complexity.linear(_RECURSION_VARIABLE)
    if frame_degree == 0:
        return ("linear", depth)
    # O(n) held per frame over O(n) frames on the path
    return ("polynomial", Complexity.power(_RECURSION_VARIABLE, frame_degree + 1))


# -- self-call discovery ----------------------------------------------------


def _self_calls(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    finder = _SelfCallFinder(func.name)
    for statement in func.body:
        finder.visit(statement)
    return finder.calls


class _SelfCallFinder(ast.NodeVisitor):
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return  # do not descend into nested definitions

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if _is_self_call(node, self.name):
            self.calls.append(node)
        self.generic_visit(node)


def _is_self_call(node: ast.Call, name: str) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == name
    if isinstance(func, ast.Attribute) and func.attr == name:
        return isinstance(func.value, ast.Name) and func.value.id == "self"
    return False


# -- branch counting ------------------------------------------------------


def _effective_branches(body: list[ast.stmt], name: str) -> int:
    return sum(_branches_in_statement(statement, name) for statement in body)


def _branches_in_statement(node: ast.stmt, name: str) -> int:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return 0

    if isinstance(node, ast.If):
        return _count_calls(node.test, name) + max(
            _effective_branches(node.body, name),
            _effective_branches(node.orelse, name),
        )

    if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
        inner = _effective_branches(node.body, name)
        # a self-call inside a loop is variable branching -> treat as exponential
        return inner * 2 if inner else 0

    if isinstance(node, (ast.With, ast.AsyncWith)):
        return _effective_branches(node.body, name)

    if isinstance(node, ast.Try):
        return (
            _effective_branches(node.body, name)
            + _effective_branches(node.orelse, name)
            + _effective_branches(node.finalbody, name)
            + sum(_effective_branches(handler.body, name) for handler in node.handlers)
        )

    return _count_calls(node, name)


def _count_calls(node: ast.AST, name: str) -> int:
    return sum(
        1
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and _is_self_call(child, name)
    )


# -- argument shrink detection -------------------------------------------


def _detect_shrink(
    func: ast.FunctionDef | ast.AsyncFunctionDef, calls: list[ast.Call]
) -> str:
    source = ast.unparse(func)
    if "// 2" in source or ">> 1" in source or "/ 2" in source:
        return "halve"

    for call in calls:
        for argument in call.args:
            if isinstance(argument, ast.Subscript):
                sliced = ast.unparse(argument)
                if "[1:]" in sliced or "[:-1]" in sliced:
                    return "subtract"
                return "halve"

    return "subtract"
