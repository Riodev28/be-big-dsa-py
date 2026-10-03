from ...shared.ast import Parser
from ...shared.ast.value_objects import NormalizedCode
from ...shared.ast.complexity import analyze_time_complexity, classify
from ..reports import TemporalAnalysisReport


class TemporalComplexityAnalyzer:
    def __init__(self, code: NormalizedCode):
        self.code = code

    def analyze(self) -> TemporalAnalysisReport:
        """Analyze big o notation complexity from the AST using the cost engine.

        The engine composes loop, branch, recursion and library-call costs into
        a symbolic expression: sequential loops add (``O(n + m)``), nested loops
        multiply and collapse to one variable (``O(n²)``), recursion is
        classified via recursion-tree reasoning (``O(log n)`` .. ``O(2^n)``).
        """

        tree = Parser.to_tree_node(self.code)
        result = analyze_time_complexity(tree)

        return TemporalAnalysisReport(
            time_complexity=result.complexity.render(),
            max_loop_depth=result.max_loop_depth,
            recursive=result.recursive,
            terms=result.complexity.term_strings(),
            variables=result.variables,
            loop_count=result.loop_count,
            recursion_kind=result.recursion_kind,
            complexity_class=classify(result.complexity),
        )
