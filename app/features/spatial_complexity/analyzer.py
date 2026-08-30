from ...shared.ast import NormalizedCode, Parser
from ...shared.ast.complexity import analyze_space_complexity
from ...shared.ast.visitors import (
    AllocationVisitors,
    DynamicGrowthVisitor,
    RecursionVisitors,
)

from ..reports import SpatialAnalysisReport


class SpatialComplexityAnalyzer:
    def __init__(self, code: NormalizedCode):
        self.code = code
        self.tree = Parser.to_tree_node(code)

    def analyze(self) -> SpatialAnalysisReport:
        """Analyze space (memory) complexity from the AST.

        The Big-O bound comes from the cost engine, which tracks collections
        that grow inside loops (``O(n)`` / ``O(n²)``), comprehensions and
        ``[0] * n`` allocations, slices/copies, and recursion **stack depth**.
        The raw allocation counts below are kept for the report / AI prompt.
        """

        # ---- COST ENGINE ----
        result = analyze_space_complexity(self.tree)

        # ---- RAW COUNTS (informational) ----
        allocation_visitor = AllocationVisitors()
        allocation_visitor.visit(self.tree)

        growth_visitor = DynamicGrowthVisitor()
        growth_visitor.visit(self.tree)

        recursion_visitor = RecursionVisitors()
        recursion_visitor.visit(self.tree)

        return SpatialAnalysisReport(
            space_complexity=result.complexity.render(),
            total_allocations=allocation_visitor.total_allocations,
            list_allocations=allocation_visitor.list_allocations,
            dict_allocations=allocation_visitor.dict_allocations,
            set_allocations=allocation_visitor.set_allocations,
            comprehensions=(
                allocation_visitor.list_comprehensions
                + allocation_visitor.dict_comprehensions
                + allocation_visitor.set_comprehensions
            ),
            generator_expressions=allocation_visitor.generator_expressions,
            dynamic_growth_operations=growth_visitor.append_calls,
            recursive_functions=len(recursion_visitor.recursive_functions),
            terms=result.complexity.term_strings(),
            variables=result.variables,
            recursion_kind=result.recursion_kind,
        )
