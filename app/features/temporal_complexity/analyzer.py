from ...shared.ast import Parser
from ...shared.ast.value_objects import NormalizedCode
from ...shared.ast.visitors import LoopVisitors, RecursionVisitors
from ..reports import TemporalAnalysisReport


class TemporalComplexityAnalyzer:
    def __init__(self, code: NormalizedCode):
        self.code = code

    def analyze(self) -> TemporalAnalysisReport:
        """Analyze big o notation complexity using the tree node and visitors"""

        tree = Parser.to_tree_node(self.code)

        loop_visitor = LoopVisitors()
        recursion_visitor = RecursionVisitors()

        loop_visitor.visit(tree)
        recursion_visitor.visit(tree)

        return self._build_result(
            loop_depth=loop_visitor.max_depth,
            recursive_functions=recursion_visitor.recursive_functions,
        )

    def _build_result(
        self, loop_depth: int, recursive_functions: set[str]
    ) -> TemporalAnalysisReport:

        complexity = self._infer_complexity(loop_depth)

        return TemporalAnalysisReport(
            time_complexity=complexity,
            max_loop_depth=loop_depth,
            recursive=bool(recursive_functions),
        )

    @staticmethod
    def _infer_complexity(loop_depth: int) -> str:
        """Complexity map for count depth loops"""
        loop_mapping = {
            0: "O(1)",
            1: "O(n)",
            2: "O(n²)",
            3: "O(n³)",
        }

        return loop_mapping.get(loop_depth, "O(n^k)")
