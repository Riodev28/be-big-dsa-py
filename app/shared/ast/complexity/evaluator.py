"""The time-complexity engine: walk an AST and compute a symbolic Big-O cost by
composing loop, branch, recursion and library-call costs.

Key rules:

* ``cost(body)`` = sum of ``cost(statement)`` -> :meth:`Complexity.add`.
* ``cost(for/while)`` = ``size(iterable) * cost(body)``.
* Nested loops **collapse to a single variable**: an inner loop reuses the
  outermost enclosing loop's symbol, so ``for/for`` is ``O(n²)`` (never
  ``O(n·m)``).
* Sequential loops over *different* iterables get ``n`` and ``m`` -> ``O(n + m)``;
  over the *same* iterable they share ``n`` -> ``O(n)``.
* Recursion is delegated to :mod:`recursion_cost`.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import reduce

from . import recursion_cost
from .expression import Complexity
from .iterable_size import callable_name, describe_iter
from .symbols import SymbolRegistry, VariableRef

# Library / builtin calls whose cost is linear in their first argument.
_LINEAR_CALLS = {
    "min",
    "max",
    "sum",
    "any",
    "all",
    "reversed",
    "list",
    "tuple",
    "set",
    "dict",
    "frozenset",
    "join",
}
# Calls whose cost is logarithmic (heap / bisect operations).
_LOGARITHMIC_CALLS = {
    "heappush",
    "heappop",
    "heapreplace",
    "heappushpop",
    "bisect",
    "bisect_left",
    "bisect_right",
    "insort",
    "insort_left",
    "insort_right",
}
_SIZE_PASS_THROUGH = {"range", "sorted", "reversed", "list", "tuple", "set"}
_VIEW_METHODS = {"items", "keys", "values"}
# Constructors that build a hash-based container (O(1) membership).
_HASH_CONSTRUCTORS = {
    "dict",
    "set",
    "frozenset",
    "defaultdict",
    "Counter",
    "OrderedDict",
}

_RECURSION_KIND_RANK = {
    None: 0,
    "none": 0,
    "logarithmic": 1,
    "linear": 2,
    "polynomial": 3,
    "divide_and_conquer": 3,
    "exponential": 4,
    "unknown": 4,
}


@dataclass(frozen=True, slots=True)
class TimeComplexityResult:
    complexity: Complexity
    max_loop_depth: int
    loop_count: int
    variables: tuple[VariableRef, ...]
    recursion_kind: str | None
    recursive: bool


def analyze_time_complexity(tree: ast.Module) -> TimeComplexityResult:
    return _CostEvaluator().analyze(tree)


class _CostEvaluator:
    def __init__(self) -> None:
        self.registry = SymbolRegistry()
        self.loop_stack: list[str] = []
        self.max_loop_depth = 0
        self.loop_count = 0
        self.call_costs: dict[str, Complexity] = {}
        self.recursive_names: set[str] = set()
        self.recursion_kind: str | None = None
        self.hash_containers: set[str] = set()

    # -- entry point ----------------------------------------------------

    def analyze(self, tree: ast.Module) -> TimeComplexityResult:
        functions = _collect_functions(tree)
        top_level = [
            node
            for node in tree.body
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            )
        ]

        self.recursive_names = {
            fn.name for fn in functions if recursion_cost.is_recursive(fn)
        }
        self.hash_containers = _find_hash_containers(tree)

        # Pass 1 warms up call_costs so pass 2 can substitute one level of calls.
        for fn in functions:
            self.call_costs[fn.name] = self._cost_of_function(fn)

        self._reset_metrics()

        # The top-level script is the entry point when it exists; functions then
        # fold in through call substitution. Recursive functions still contribute
        # directly (a recursive call substitutes to O(1) on its own).
        top_cost = self._cost_of_body(top_level) if top_level else None

        recursive_cost = Complexity.constant()
        library_costs: list[Complexity] = []
        for fn in functions:
            cost = self._cost_of_function(fn)
            if fn.name in self.recursive_names:
                recursive_cost = recursive_cost.add(cost)
            else:
                library_costs.append(cost)

        if top_cost is not None:
            module_cost = top_cost.add(recursive_cost)
        else:
            module_cost = reduce(
                lambda left, right: left.add(right), library_costs, recursive_cost
            )

        used = {symbol for term in module_cost.terms for symbol, _ in term.powers}
        variables = tuple(
            ref for ref in self.registry.variables() if ref.symbol in used
        )

        return TimeComplexityResult(
            complexity=module_cost,
            max_loop_depth=self.max_loop_depth,
            loop_count=self.loop_count,
            variables=variables,
            recursion_kind=self.recursion_kind,
            recursive=bool(self.recursive_names),
        )

    def _reset_metrics(self) -> None:
        self.registry = SymbolRegistry()
        self.loop_stack = []
        self.max_loop_depth = 0
        self.loop_count = 0
        self.recursion_kind = None

    # -- functions ----------------------------------------------------

    def _cost_of_function(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Complexity:
        recursive = func.name in self.recursive_names
        outer_stack = self.loop_stack
        outer_registry = self.registry
        self.loop_stack = []
        if recursive:
            # The recursion classifier reports in the canonical variable `n`; a
            # throwaway registry keeps the body's loop symbols from leaking.
            self.registry = SymbolRegistry()
        try:
            body_cost = self._cost_of_body(func.body)
        finally:
            self.loop_stack = outer_stack
            self.registry = outer_registry

        if not recursive:
            return body_cost

        kind, complexity = recursion_cost.classify(func, body_cost)
        self._record_recursion_kind(kind)
        return complexity

    def _record_recursion_kind(self, kind: str) -> None:
        best = _RECURSION_KIND_RANK.get(self.recursion_kind, 0)
        if _RECURSION_KIND_RANK.get(kind, 0) > best:
            self.recursion_kind = kind
        elif self.recursion_kind is None and kind not in (None, "none"):
            self.recursion_kind = kind

    # -- statements -------------------------------------------------

    def _cost_of_body(self, statements: list[ast.stmt]) -> Complexity:
        cost = Complexity.constant()
        for statement in statements:
            cost = cost.add(self._cost_of_statement(statement))
        return cost

    def _cost_of_statement(self, node: ast.stmt) -> Complexity:
        if isinstance(node, (ast.For, ast.AsyncFor)):
            return self._cost_of_loop(node, node.iter)
        if isinstance(node, ast.While):
            return self._cost_of_loop(node, None)
        if isinstance(node, ast.If):
            return (
                self._cost_of_expression(node.test)
                .add(self._cost_of_body(node.body))
                .add(self._cost_of_body(node.orelse))
            )
        if isinstance(node, (ast.With, ast.AsyncWith)):
            return self._cost_of_body(node.body)
        if isinstance(node, ast.Try):
            return reduce(
                lambda left, right: left.add(right),
                [
                    self._cost_of_body(node.body),
                    self._cost_of_body(node.orelse),
                    self._cost_of_body(node.finalbody),
                    *(self._cost_of_body(handler.body) for handler in node.handlers),
                ],
                Complexity.constant(),
            )
        if isinstance(node, ast.ClassDef):
            return self._cost_of_body(node.body)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return Complexity.constant()  # only contributes when called
        if isinstance(
            node, (ast.Return, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr)
        ):
            value = getattr(node, "value", None)
            if value is None:
                return Complexity.constant()
            return self._cost_of_expression(value)
        return Complexity.constant()

    def _cost_of_loop(self, node: ast.stmt, iterable: ast.expr | None) -> Complexity:
        self.loop_count += 1

        sorts = False
        logarithmic = False
        if iterable is not None:
            info = describe_iter(iterable)
            key = info.key
            sorts = info.sorts
        else:  # while loop
            key = ast.unparse(node.test)
            logarithmic = _looks_like_halving(node)

        if key is None:
            symbol: str | None = None
        elif self.loop_stack:
            symbol = self.loop_stack[0]  # collapse rule
        else:
            symbol = self.registry.symbol_for(key)

        pushed = symbol is not None
        if pushed:
            self.loop_stack.append(symbol)
            self.max_loop_depth = max(self.max_loop_depth, len(self.loop_stack))

        body_cost = self._cost_of_body(node.body)
        orelse = getattr(node, "orelse", [])
        else_cost = self._cost_of_body(orelse) if orelse else Complexity.constant()

        if pushed:
            self.loop_stack.pop()

        if symbol is None:
            factor = Complexity.constant()
        elif logarithmic:
            factor = Complexity.logarithmic()
        else:
            factor = Complexity.linear(symbol)

        result = factor.multiply(body_cost)
        if sorts and symbol is not None:
            result = result.add(Complexity.linear(symbol).times_log())
        return result.add(else_cost)

    # -- expressions -----------------------------------------------

    def _cost_of_expression(self, node: ast.expr | None) -> Complexity:
        if node is None:
            return Complexity.constant()
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self._cost_of_comprehension(node.generators, [node.elt])
        if isinstance(node, ast.DictComp):
            return self._cost_of_comprehension(node.generators, [node.key, node.value])
        if isinstance(node, ast.Call):
            return self._cost_of_call(node)
        if isinstance(node, ast.Compare):
            return self._cost_of_compare(node)
        if isinstance(node, ast.BoolOp):
            return self._reduce_expressions(node.values)
        if isinstance(node, ast.BinOp):
            return self._cost_of_expression(node.left).add(
                self._cost_of_expression(node.right)
            )
        if isinstance(node, ast.UnaryOp):
            return self._cost_of_expression(node.operand)
        if isinstance(node, ast.IfExp):
            return (
                self._cost_of_expression(node.test)
                .add(self._cost_of_expression(node.body))
                .add(self._cost_of_expression(node.orelse))
            )
        if isinstance(node, ast.Subscript):
            return self._cost_of_expression(node.value).add(
                self._cost_of_expression(node.slice)
            )
        if isinstance(node, (ast.Await, ast.Starred, ast.Yield, ast.YieldFrom)):
            return self._cost_of_expression(getattr(node, "value", None))
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return self._reduce_expressions(node.elts)
        return Complexity.constant()

    def _reduce_expressions(self, nodes: list[ast.expr]) -> Complexity:
        return reduce(
            lambda left, right: left.add(right),
            (self._cost_of_expression(child) for child in nodes),
            Complexity.constant(),
        )

    def _cost_of_comprehension(
        self, generators: list[ast.comprehension], elements: list[ast.expr]
    ) -> Complexity:
        local_stack = list(self.loop_stack)
        factor = Complexity.constant()
        extra = Complexity.constant()

        for generator in generators:
            info = describe_iter(generator.iter)
            if info.key is not None:
                if local_stack:
                    symbol = local_stack[0]  # collapse rule
                else:
                    symbol = self.registry.symbol_for(info.key)
                local_stack.append(symbol)
                factor = factor.multiply(Complexity.linear(symbol))
                if info.sorts:
                    extra = extra.add(Complexity.linear(symbol).times_log())
            for condition in generator.ifs:
                extra = extra.add(self._cost_of_expression(condition))

        return factor.multiply(self._reduce_expressions(elements)).add(extra)

    def _cost_of_compare(self, node: ast.Compare) -> Complexity:
        cost = self._cost_of_expression(node.left)
        for operator, comparator in zip(node.ops, node.comparators):
            if isinstance(operator, (ast.In, ast.NotIn)):
                cost = cost.add(self._membership_cost(comparator))
            cost = cost.add(self._cost_of_expression(comparator))
        return cost

    def _membership_cost(self, container: ast.expr) -> Complexity:
        # Hash-based containers (set/dict, literal or named) -> O(1) membership.
        if isinstance(container, (ast.Set, ast.Dict, ast.List, ast.Tuple)):
            return Complexity.constant()
        if (
            isinstance(container, ast.Call)
            and callable_name(container) in _HASH_CONSTRUCTORS
        ):
            return Complexity.constant()
        if isinstance(container, (ast.Name, ast.Attribute)):
            key = (
                container.id
                if isinstance(container, ast.Name)
                else ast.unparse(container)
            )
            if key in self.hash_containers:
                return Complexity.constant()
            return Complexity.linear(self._size_symbol(key))
        return Complexity.constant()

    def _cost_of_call(self, node: ast.Call) -> Complexity:
        name = callable_name(node)
        arguments_cost = self._reduce_expressions(
            [*node.args, *(keyword.value for keyword in node.keywords)]
        )

        if name is None:
            return arguments_cost

        if name in self.recursive_names:
            return arguments_cost  # recursion handled by the classifier

        if name == "sorted" and node.args:
            return self._expression_size(node.args[0]).times_log().add(arguments_cost)

        if name == "sort" and isinstance(node.func, ast.Attribute):
            return (
                self._expression_size(node.func.value).times_log().add(arguments_cost)
            )

        if name in _LINEAR_CALLS:
            first = (
                self._expression_size(node.args[0])
                if node.args
                else Complexity.constant()
            )
            return first.add(arguments_cost)

        if name in _LOGARITHMIC_CALLS:
            return Complexity.logarithmic().add(arguments_cost)

        if name in self.call_costs:
            return self._substituted_call_cost(self.call_costs[name]).add(
                arguments_cost
            )

        return arguments_cost

    def _substituted_call_cost(self, cost: Complexity) -> Complexity:
        if cost.is_constant():
            return Complexity.constant()
        if cost.is_exponential():
            return Complexity.exponential()
        symbol = (
            self.loop_stack[0] if self.loop_stack else self.registry.symbol_for("call")
        )
        result = (
            Complexity.power(symbol, cost.max_degree())
            if cost.max_degree()
            else Complexity.constant()
        )
        return result.times_log() if cost.has_log() else result

    def _expression_size(self, node: ast.expr) -> Complexity:
        if isinstance(node, ast.Name):
            return Complexity.linear(self._size_symbol(node.id))
        if isinstance(node, (ast.Attribute, ast.Subscript)):
            return Complexity.linear(self._size_symbol(ast.unparse(node)))
        if isinstance(node, ast.Call):
            name = callable_name(node)
            if name in _SIZE_PASS_THROUGH and node.args:
                return self._expression_size(node.args[0])
            if isinstance(node.func, ast.Attribute) and node.func.attr in _VIEW_METHODS:
                return Complexity.linear(
                    self._size_symbol(ast.unparse(node.func.value))
                )
        return Complexity.constant()

    def _size_symbol(self, key: str) -> str:
        if self.loop_stack:
            return self.loop_stack[0]
        return self.registry.symbol_for(key)


def _collect_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
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


def _looks_like_halving(node: ast.stmt) -> bool:
    source = ast.unparse(node)
    return "// 2" in source or ">> 1" in source


def _find_hash_containers(tree: ast.Module) -> set[str]:
    """Names bound anywhere to a dict/set-like value; membership in them is O(1)."""
    finder = _HashContainerFinder()
    finder.visit(tree)
    return finder.names


class _HashContainerFinder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        if _is_hash_container(node.value):
            for target in node.targets:
                self._record(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and _is_hash_container(node.value):
            self._record(node.target)
        self.generic_visit(node)

    def _record(self, target: ast.expr) -> None:
        if isinstance(target, ast.Name):
            self.names.add(target.id)
        elif isinstance(target, ast.Attribute):
            self.names.add(ast.unparse(target))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._record(element)


def _is_hash_container(node: ast.expr) -> bool:
    if isinstance(node, (ast.Dict, ast.DictComp, ast.Set, ast.SetComp)):
        return True
    if isinstance(node, ast.Call):
        return callable_name(node) in _HASH_CONSTRUCTORS
    return False
