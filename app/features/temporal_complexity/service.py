from typing import Any

from ...shared.ast.fingerprint import Fingerprint
from ...shared.ast.value_objects.normalized_code import NormalizedCode
from ...shared.cache.mixin import CacheMixin
from ...shared.cache.service import CacheService
from ...shared.ai.service import AIService

from .analyzer import TemporalComplexityAnalyzer
from .request import TemporalComplexityRequest
from .dto import TemporalComplexityResponseDTO

from ..reports import (
    TemporalAnalysisReport,
    TemporalAIReport,
)


class TemporalComplexityService(CacheMixin):
    def __init__(self, cache_client: CacheService, ai_service: AIService):
        self.cache_service = cache_client
        self.ai_service = ai_service

    async def analyze(self, payload: TemporalComplexityRequest):
        """Orchestrate payload. Analyze time complexity result"""
        normalized_code = NormalizedCode(payload.code)

        fingerprint = Fingerprint(normalized_code)

        analysis_key, cached_analysis = self.process_cache(
            "temporal_complexity", fingerprint
        )

        if cached_analysis:
            report = TemporalAnalysisReport.from_cache(cached_analysis)

        else:
            report = TemporalComplexityAnalyzer(normalized_code).analyze()
            self.cache_service.set_cache(analysis_key, report)

        ai_report = None

        if payload.explain_ai:
            ai_key, cached_ai = self.process_cache(
                "temporal_complexity_ai", fingerprint
            )

            ai_report = await self._handle_ai(
                key=ai_key, cached=cached_ai, report=report
            )

        return TemporalComplexityResponseDTO(analysis=report, ai=ai_report)

    async def _handle_ai(
        self, key: str, cached: dict[str, Any] | None, report: TemporalAnalysisReport
    ) -> TemporalAIReport | None:
        if cached:
            return TemporalAIReport(**cached)

        explanation = await self.ai_service.explain_temporal_complexity(
            time_complexity=report.time_complexity,
            max_loop_depth=report.max_loop_depth,
            recursive=report.recursive,
            terms=report.terms,
            variables=report.variables,
            recursion_kind=report.recursion_kind,
        )

        ai_report = TemporalAIReport(temporal_explanation=explanation)

        self.cache_service.set_cache(key, ai_report, ex_ttl=86400)

        return ai_report
