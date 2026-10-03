from typing import Any

from ...shared.analysis import AnalysisKind, ComplexityAnalysisService
from ...shared.ast.complexity import ComplexityClass
from ...shared.ast.value_objects.normalized_code import NormalizedCode
from ..reports import TemporalAIReport, TemporalAnalysisReport
from .analyzer import TemporalComplexityAnalyzer
from .dto import TemporalComplexityResponseDTO
from .request import TemporalComplexityRequest


class TemporalComplexityService(
    ComplexityAnalysisService[TemporalAnalysisReport, TemporalAIReport]
):
    kind = AnalysisKind.TEMPORAL
    # v2: reports gained `complexity_class`, older cached entries lack it
    cache_namespace = "temporal_complexity:v2"
    ai_cache_namespace = "temporal_complexity_ai"

    async def analyze(
        self, payload: TemporalComplexityRequest, user_id: str | None = None
    ) -> TemporalComplexityResponseDTO:
        """Orchestrate payload. Analyze time complexity result"""
        outcome = await self.run(payload, user_id)
        return TemporalComplexityResponseDTO(analysis=outcome.report, ai=outcome.ai)

    def _analyze(self, code: NormalizedCode) -> TemporalAnalysisReport:
        return TemporalComplexityAnalyzer(code).analyze()

    def _report_from_cache(self, data: dict[str, Any]) -> TemporalAnalysisReport:
        return TemporalAnalysisReport.from_cache(data)

    def _ai_report_from_cache(self, data: dict[str, Any]) -> TemporalAIReport:
        return TemporalAIReport(**data)

    async def _explain(self, report: TemporalAnalysisReport) -> TemporalAIReport:
        explanation = await self.ai_service.explain_temporal_complexity(
            time_complexity=report.time_complexity,
            max_loop_depth=report.max_loop_depth,
            recursive=report.recursive,
            terms=report.terms,
            variables=report.variables,
            recursion_kind=report.recursion_kind,
        )
        return TemporalAIReport(temporal_explanation=explanation)

    def _notation(self, report: TemporalAnalysisReport) -> str:
        return report.time_complexity

    def _complexity_class(self, report: TemporalAnalysisReport) -> ComplexityClass:
        return report.complexity_class
