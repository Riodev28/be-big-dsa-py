"""The space-complexity engine: walk an AST and compute a symbolic Big-O bound
on the *extra* memory an algorithm allocates as a function of input size.

What counts:

* Collections that grow inside loops (``res.append`` / ``d[k] = v`` / ``+=``):
  size = product of the enclosing loop factors, collapsed to one variable
  (a list filled in a double loop is ``O(n²)``).
* Comprehensions and ``[0] * n`` style allocations.
* Slices / copies (``arr[a:b]``, ``list(x)``, ``sorted(x)``, ``a + b``).
* Recursion **stack depth** (``O(log n)`` for halving, ``O(n)`` otherwise) -
  note this is depth, not call count, so tree recursion is ``O(n)`` space.

What does not: in-place work, scalars, and generator expressions (lazy -> O(1)).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import reduce

from . import recursion_cost
from .expression import Complexity
from .helpers import collect_functions
from .iterable_size import callable_name, describe_iter
from .symbols import SymbolRegistry, VariableRef

# Calls that allocate a copy the size of their first argument.
_COPY_CALLS = {"list", "set", "tuple", "dict", "sorted", "frozenset", "Counter"}
# Calls that allocate nothing eagerly.
_LAZY_CALLS = {"range", "enumerate", "zip", "reversed", "iter", "map", "filter"}
_GROWTH_METHODS = {"append", "add", "update", "extend", "insert", "appendleft"}
_VIEW_METHODS = {"items", "keys", "values"}


@dataclass(frozen=True, slots=True)
class SpaceComplexityResult:
    complexity: Complexity
    variables: tuple[VariableRef, ...]
    recursion_kind: str | None
    recursive: bool


def analyze_space_complexity(tree: ast.Module) -> SpaceComplexityResult:
    return _SpaceEvaluator().analyze(tree)


class _SpaceEvaluator:
    def __init__(self) -> None:
        self.registry = SymbolRegistry()
        self.scale_stack: list[str] = []
        self.holds: dict[str, Complexity] = {}
        self.growth: dict[str, Complexity] = {}
        self.assigned_depth: dict[str, int] = {}
        self.peak = Complexity.constant()
        self.call_space: dict[str, Complexity] = {}
        self.recursive_names: set[str] = set()
        self.recursion_kind: str | None = None

    # -- entry point --------------------------------------------------

    def analyze(self, tree: ast.Module) -> SpaceComplexityResult:
        functions = collect_functions(tree)
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

        for fn in functions:
            self.call_space[fn.name] = self._space_of_function(fn)

        self._reset()
        top_space = self._walk_scope(top_level) if top_level else None

        recursive_space = Complexity.constant()
        library_space: list[Complexity] = []
        for fn in functions:
            space = self._space_of_function(fn)
            if fn.name in self.recursive_names:
                recursive_space = recursive_space.add(space)
            else:
                library_space.append(space)

        if top_space is not None:
            module_space = top_space.add(recursive_space)
        else:
            module_space = reduce(
                lambda left, right: left.add(right), library_space, recursive_space
            )

        used = {symbol for term in module_space.terms for symbol, _ in term.powers}
        variables = tuple(
            ref for ref in self.registry.variables() if ref.symbol in used
        )

        return SpaceComplexityResult(
            complexity=module_space,
            variables=variables,
            recursion_kind=self.recursion_kind,
            recursive=bool(self.recursive_names),
        )

    def _reset(self) -> None:
        self.registry = SymbolRegistry()
        self.scale_stack = []
        self.recursion_kind = None
        self._reset_scope()

    def _reset_scope(self) -> None:
        self.holds = {}
        self.growth = {}
        self.assigned_depth = {}
        self.peak = Complexity.constant()

    # -- scopes ---------------------------------------------------------

    def _walk_scope(self, statements: list[ast.stmt]) -> Complexity:
        saved = (self.holds, self.growth, self.assigned_depth, self.peak)
        self._reset_scope()
        for statement in statements:
            self._walk_statement(statement)
        scope_space = reduce(
            lambda left, right: left.add(right),
            self.growth.values(),
            self.peak,
        )
        self.holds, self.growth, self.assigned_depth, self.peak = saved
        return scope_space

    def _space_of_function(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Complexity:
        recursive = func.name in self.recursive_names
        saved_stack = self.scale_stack
        saved_registry = self.registry
        self.scale_stack = []
        if recursive:
            self.registry = SymbolRegistry()
        try:
            body_space = self._walk_scope(func.body)
        finally:
            self.scale_stack = saved_stack
            self.registry = saved_registry

        if not recursive:
            return body_space

        kind, stack_space = recursion_cost.classify_space(func, _frame_allocation(func))
        self._record_recursion_kind(kind)
        return body_space.add(stack_space)

    def _record_recursion_kind(self, kind: str) -> None:
        rank = recursion_cost.SPACE_KIND_RANK
        if rank.get(kind, 0) > rank.get(self.recursion_kind, 0):
            self.recursion_kind = kind
        elif self.recursion_kind is None and kind not in (None, "none"):
            self.recursion_kind = kind

    # -- statements -------------------------------------------------

    def _walk_statement(self, node: ast.stmt) -> None:
        if isinstance(node, (ast.For, ast.AsyncFor)):
            self._walk_loop(node, node.iter)
        elif isinstance(node, ast.While):
            self._walk_loop(node, None)
        elif isinstance(node, ast.If):
            self._note(node.test)
            self._walk_body(node.body)
            self._walk_body(node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            self._walk_body(node.body)
        elif isinstance(node, ast.Try):
            self._walk_body(node.body)
            self._walk_body(node.orelse)
            self._walk_body(node.finalbody)
            for handler in node.handlers:
                self._walk_body(handler.body)
        elif isinstance(node, ast.ClassDef):
            self._walk_body(node.body)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return  # only contributes when called
        elif isinstance(node, ast.Assign):
            self._walk_assign(node.targets, node.value)
        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._walk_assign([node.target], node.value)
        elif isinstance(node, ast.AugAssign):
            self._note(node.value)
            if isinstance(node.target, ast.Name):
                self._record_growth(node.target.id, node.value)
        elif isinstance(node, (ast.Return, ast.Expr)):
            if node.value is not None:
                self._note(node.value)

    def _walk_body(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self._walk_statement(statement)

    def _walk_loop(self, node: ast.stmt, iterable: ast.expr | None) -> None:
        if iterable is not None:
            info = describe_iter(iterable)
            key = info.key
        else:
            key = ast.unparse(node.test)

        if key is None:
            symbol = None
        elif self.scale_stack:
            symbol = self.scale_stack[0]  # collapse rule
        else:
            symbol = self.registry.symbol_for(key)

        if symbol is not None:
            self.scale_stack.append(symbol)
        self._walk_body(node.body)
        self._walk_body(getattr(node, "orelse", []))
        if symbol is not None:
            self.scale_stack.pop()

    def _walk_assign(self, targets: list[ast.expr], value: ast.expr) -> None:
        size = self._size_of(value)
        self.peak = self.peak.add(size)

        for target in targets:
            if isinstance(target, ast.Name):
                self.holds[target.id] = size
                self.growth.pop(target.id, None)
                self.assigned_depth[target.id] = len(self.scale_stack)
            elif isinstance(target, ast.Subscript) and isinstance(
                target.value, ast.Name
            ):
                self._record_growth(target.value.id, value)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        self.holds[element.id] = Complexity.constant()

        self._note(value)

    # -- growth attribution --------------------------------------

    def _record_growth(self, name: str, element: ast.expr | None) -> None:
        if name not in self.holds and name not in self.assigned_depth:
            return  # unknown container (probably an argument) - not aux space

        start = self.assigned_depth.get(name, 0)
        scales = self.scale_stack[start:]
        count = reduce(
            lambda acc, symbol: acc.multiply(Complexity.linear(symbol)),
            scales,
            Complexity.constant(),
        )
        element_size = (
            self._size_of(element) if element is not None else Complexity.constant()
        )
        contribution = count.multiply(element_size)
        self.growth[name] = self.growth.get(name, Complexity.constant()).add(
            contribution
        )

    # -- expression sizing -----------------------------------------

    def _note(self, node: ast.expr) -> None:
        """Record any allocation that happens while evaluating *node*."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                method = _method_call_target(child)
                if method is not None and _method_name(child) in _GROWTH_METHODS:
                    element = child.args[0] if child.args else None
                    self._record_growth(method, element)
            if isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp)):
                self.peak = self.peak.add(self._size_of(child))

    def _size_of(self, node: ast.expr) -> Complexity:
        """The allocation size of an expression, as a Big-O bound."""
        if isinstance(node, ast.GeneratorExp):
            return Complexity.constant()  # lazy
        if isinstance(node, (ast.ListComp, ast.SetComp)):
            return self._comprehension_size(node.generators, [node.elt])
        if isinstance(node, ast.DictComp):
            return self._comprehension_size(node.generators, [node.key, node.value])
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return reduce(
                lambda left, right: left.add(right),
                (self._size_of(element) for element in node.elts),
                Complexity.constant(),
            )
        if isinstance(node, ast.Dict):
            return reduce(
                lambda left, right: left.add(right),
                (self._size_of(value) for value in node.values if value is not None),
                Complexity.constant(),
            )
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Mult):
                return self._repeat_size(node.left, node.right)
            if isinstance(node.op, ast.Add):
                return self._size_of(node.left).add(self._size_of(node.right))
            return Complexity.constant()
        if isinstance(node, ast.Call):
            return self._call_size(node)
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                return self._value_size(node.value)
            return Complexity.constant()
        if isinstance(node, ast.Name):
            return self.holds.get(node.id, Complexity.constant()).add(
                self.growth.get(node.id, Complexity.constant())
            )
        if isinstance(node, ast.IfExp):
            return self._size_of(node.body).add(self._size_of(node.orelse))
        if isinstance(node, ast.Starred):
            return self._size_of(node.value)
        return Complexity.constant()

    def _repeat_size(self, left: ast.expr, right: ast.expr) -> Complexity:
        for collection, count in ((left, right), (right, left)):
            if not _is_sequence_literal(collection):
                continue
            if isinstance(count, ast.Constant):
                return Complexity.constant()
            return self._value_size(count)
        return Complexity.constant()

    def _call_size(self, node: ast.Call) -> Complexity:
        name = callable_name(node)
        if name in self.recursive_names:
            return Complexity.constant()  # stack handled by the classifier
        if name in _LAZY_CALLS:
            return Complexity.constant()
        if name in _COPY_CALLS and node.args:
            return self._value_size(node.args[0])
        if name == "copy" and isinstance(node.func, ast.Attribute):
            return self._value_size(node.func.value)
        if name in self.call_space:
            return self._substituted(self.call_space[name])
        return Complexity.constant()

    def _comprehension_size(
        self, generators: list[ast.comprehension], elements: list[ast.expr]
    ) -> Complexity:
        local = list(self.scale_stack)
        factor = Complexity.constant()
        for generator in generators:
            info = describe_iter(generator.iter)
            if info.key is None:
                continue
            symbol = local[0] if local else self.registry.symbol_for(info.key)
            local.append(symbol)
            factor = factor.multiply(Complexity.linear(symbol))

        element_size = reduce(
            lambda left, right: left.add(right),
            (self._size_in_scope(element, local) for element in elements),
            Complexity.constant(),
        )
        return factor.multiply(element_size)

    def _size_in_scope(self, node: ast.expr, scale: list[str]) -> Complexity:
        saved = self.scale_stack
        self.scale_stack = scale
        try:
            return self._size_of(node)
        finally:
            self.scale_stack = saved

    def _value_size(self, node: ast.expr) -> Complexity:
        """A Big-O bound linear in the size of an existing value."""
        if isinstance(node, ast.Name):
            return Complexity.linear(self._scale_symbol(node.id))
        if isinstance(node, (ast.Attribute, ast.Subscript)):
            return Complexity.linear(self._scale_symbol(ast.unparse(node)))
        if isinstance(node, ast.Call):
            name = callable_name(node)
            if name in _COPY_CALLS | _LAZY_CALLS and node.args:
                return self._value_size(node.args[0])
            if isinstance(node.func, ast.Attribute) and node.func.attr in _VIEW_METHODS:
                return Complexity.linear(
                    self._scale_symbol(ast.unparse(node.func.value))
                )
        return Complexity.constant()

    def _substituted(self, space: Complexity) -> Complexity:
        if space.is_constant():
            return Complexity.constant()
        if space.is_exponential():
            return Complexity.exponential()
        symbol = (
            self.scale_stack[0]
            if self.scale_stack
            else self.registry.symbol_for("call")
        )
        result = (
            Complexity.power(symbol, space.max_degree())
            if space.max_degree()
            else Complexity.constant()
        )
        return result.times_log() if space.has_log() else result

    def _scale_symbol(self, key: str) -> str:
        if self.scale_stack:
            return self.scale_stack[0]
        return self.registry.symbol_for(key)


def _is_sequence_literal(node: ast.expr) -> bool:
    if isinstance(node, (ast.List, ast.Tuple)):
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


def _method_call_target(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return node.func.value.id
    return None


def _method_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _frame_allocation(func: ast.FunctionDef | ast.AsyncFunctionDef) -> Complexity:
    """Non-constant memory each recursion frame holds onto (a slice / copy)."""
    for node in ast.walk(func):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return Complexity.linear("n")
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
            return Complexity.linear("n")
        if isinstance(node, ast.Call) and callable_name(node) in {
            "list",
            "sorted",
            "set",
            "tuple",
            "dict",
        }:
            return Complexity.linear("n")
    return Complexity.constant()
