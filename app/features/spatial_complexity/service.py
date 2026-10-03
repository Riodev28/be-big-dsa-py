from typing import Any

from ...shared.analysis import AnalysisKind, ComplexityAnalysisService
from ...shared.ast import NormalizedCode
from ...shared.ast.complexity import ComplexityClass
from ..reports import SpatialAiReport, SpatialAnalysisReport
from .analyzer import SpatialComplexityAnalyzer
from .dto import SpatialComplexityResponseDTO
from .request import SpatialComplexityRequest


class SpatialComplexityService(
    ComplexityAnalysisService[SpatialAnalysisReport, SpatialAiReport]
):
    kind = AnalysisKind.SPATIAL
    # v2: reports gained `complexity_class`, older cached entries lack it
    cache_namespace = "spatial_complexity:v2"
    ai_cache_namespace = "spatial_complexity_ai"

    async def analyze(
        self, payload: SpatialComplexityRequest, user_id: str | None = None
    ) -> SpatialComplexityResponseDTO:
        """Orchestrate payload. Analyze spatial complexity result"""
        outcome = await self.run(payload, user_id)
        return SpatialComplexityResponseDTO(analysis=outcome.report, ai=outcome.ai)

    def _analyze(self, code: NormalizedCode) -> SpatialAnalysisReport:
        return SpatialComplexityAnalyzer(code).analyze()

    def _report_from_cache(self, data: dict[str, Any]) -> SpatialAnalysisReport:
        return SpatialAnalysisReport.from_cache(data)

    def _ai_report_from_cache(self, data: dict[str, Any]) -> SpatialAiReport:
        return SpatialAiReport(**data)

    async def _explain(self, report: SpatialAnalysisReport) -> SpatialAiReport:
        explanation = await self.ai_service.explain_spatial_complexity(
            space_complexity=report.space_complexity,
            total_allocations=report.total_allocations,
            list_allocations=report.list_allocations,
            dict_allocations=report.dict_allocations,
            set_allocations=report.set_allocations,
            comprehensions=report.comprehensions,
            recursive_functions=report.recursive_functions,
            generator_expressions=report.generator_expressions,
            dynamic_growth_operations=report.dynamic_growth_operations,
            terms=report.terms,
            variables=report.variables,
            recursion_kind=report.recursion_kind,
        )
        return SpatialAiReport(spatial_explanation=explanation)

    def _notation(self, report: SpatialAnalysisReport) -> str:
        return report.space_complexity

    def _complexity_class(self, report: SpatialAnalysisReport) -> ComplexityClass:
        return report.complexity_class
