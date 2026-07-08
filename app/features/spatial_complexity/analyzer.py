import ast

from ...shared.ast import NormalizedCode
from ...shared.ast.visitors import (
    AllocationVisitors,
    DynamicGrowthVisitor,
    RecursionVisitors,
)

from ..reports import SpatialAnalysisReport


class SpatialComplexityAnalyzer:
    def __init__(self, code: NormalizedCode):
        self.code = code
        self.tree = ast.parse(code.value())

    def analyze(self) -> SpatialAnalysisReport:

        # -------------------------
        # VISITORS
        # -------------------------

        allocation_visitor = AllocationVisitors()
        allocation_visitor.visit(self.tree)

        growth_visitor = DynamicGrowthVisitor()
        growth_visitor.visit(self.tree)

        recursion_visitor = RecursionVisitors()
        recursion_visitor.visit(self.tree)

        # -------------------------
        # METRICS
        # -------------------------

        total_allocations = allocation_visitor.total_allocations

        dynamic_growth = growth_visitor.append_calls

        recursive_functions = len(recursion_visitor.recursive_functions)

        # -------------------------
        # COMPLEXITY INFERENCE
        # -------------------------

        complexity = self._infer_complexity(
            total_allocations=total_allocations,
            dynamic_growth=dynamic_growth,
            recursive_functions=recursive_functions,
        )

        # -------------------------
        # REPORT
        # -------------------------

        return SpatialAnalysisReport(
            space_complexity=complexity,
            total_allocations=total_allocations,
            list_allocations=allocation_visitor.list_allocations,
            dict_allocations=allocation_visitor.dict_allocations,
            set_allocations=allocation_visitor.set_allocations,
            comprehensions=allocation_visitor.set_comprehensions,
            generator_expressions=allocation_visitor.generator_expressions,
            dynamic_growth_operations=dynamic_growth,
            recursive_functions=recursive_functions,
        )

    @staticmethod
    def _infer_complexity(
        total_allocations: int,
        dynamic_growth: int,
        recursive_functions: int,
    ) -> str:

        # Recursive stack usage or Growing containers
        if recursive_functions > 0 or dynamic_growth > 0:
            return "O(n)"

        # No allocations
        if total_allocations == 0:
            return "O(1)"

        # Many allocations
        if total_allocations > 10:
            return "O(n²)"

        return "O(1)"
