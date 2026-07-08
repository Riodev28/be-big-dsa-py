from .request import SpatialComplexityRequest
from ...shared.ai.service import AIService
from ...shared.cache import CacheService
from ...shared.ast import NormalizedCode, Fingerprint
from .dto import SpatialComplexityResponseDTO
from ...shared.cache.mixin import CacheMixin
from ..reports import SpatialAnalysisReport, SpatialAiReport
from typing import Any
from .analyzer import SpatialComplexityAnalyzer


class SpatialComplexityService(CacheMixin):
    def __init__(self, cache: CacheService, ai: AIService):
        self.cache_service = cache
        self.ai_service = ai

    async def analyze(
        self, payload: SpatialComplexityRequest
    ) -> SpatialComplexityResponseDTO:
        """Orchestrate payload. Analyze spatial complexity result"""
        normalized_code = NormalizedCode(payload.code)

        fingerprint = Fingerprint(normalized_code)

        analysis_key, cached_analysis = self.process_cache(
            "spatial_complexity", fingerprint
        )

        if cached_analysis:
            report = SpatialAnalysisReport(**cached_analysis)

        else:
            report = SpatialComplexityAnalyzer(normalized_code).analyze()
            self.cache_service.set_cache(analysis_key, report)

        ai_report = None

        if payload.explain_ai:
            ai_key, cached_ai = self.process_cache("spatial_complexity_ai", fingerprint)

            ai_report = await self._handle_ai(
                key=ai_key, cached=cached_ai, report=report
            )

        return SpatialComplexityResponseDTO(analysis=report, ai=ai_report)

    async def _handle_ai(
        self, key: str, cached: dict[str, Any] | None, report: SpatialAnalysisReport
    ) -> SpatialAnalysisReport | None:
        if cached:
            return SpatialAiReport(**cached)

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
        )

        ai_report = SpatialAiReport(spatial_explanation=explanation)

        self.cache_service.set_cache(key, ai_report, ex_ttl=86400)

        return ai_report
