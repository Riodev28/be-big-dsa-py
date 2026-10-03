import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Generic, TypeVar

import anyio

from app.shared.ai.service import AIService
from app.shared.ast import Fingerprint, NormalizedCode
from app.shared.ast.complexity import ComplexityClass
from app.shared.cache.mixin import CacheMixin
from app.shared.cache.service import CacheService

from .recording import AnalysisKind, AnalysisRecord, AnalysisRecorder, NullAnalysisRecorder
from .request import AnalysisRequest

logger = logging.getLogger(__name__)

# The analyzers parse with the server's own `ast`, so that is the grammar used
ANALYZED_LANGUAGE = f"Python {sys.version_info.major}.{sys.version_info.minor}"
AI_CACHE_TTL_SECONDS = 86400

ReportT = TypeVar("ReportT")
AIReportT = TypeVar("AIReportT")


@dataclass(frozen=True)
class AnalysisOutcome(Generic[ReportT, AIReportT]):
    report: ReportT
    ai: AIReportT | None


class ComplexityAnalysisService(CacheMixin, ABC, Generic[ReportT, AIReportT]):
    """
    Template Method: `run` owns the workflow shared by every analysis kind
    (normalize -> cached analysis -> optional AI -> record). Subclasses only
    fill in the hooks that differ: how to analyze, rebuild from cache and
    explain.
    """

    kind: ClassVar[AnalysisKind]
    cache_namespace: ClassVar[str]
    ai_cache_namespace: ClassVar[str]

    def __init__(
        self,
        cache: CacheService,
        ai: AIService,
        recorder: AnalysisRecorder | None = None,
    ):
        self.cache_service = cache
        self.ai_service = ai
        self.recorder = recorder or NullAnalysisRecorder()

    async def run(
        self, request: AnalysisRequest, user_id: str | None
    ) -> AnalysisOutcome[ReportT, AIReportT]:
        code = NormalizedCode(request.code)
        fingerprint = Fingerprint(code)

        started = time.perf_counter()
        report, cached = self._get_report(code, fingerprint)
        duration_ms = (time.perf_counter() - started) * 1000

        ai_report = (
            await self._get_ai_report(fingerprint, report) if request.explain_ai else None
        )

        # Only signed-in users have a history; anonymous runs are not stored
        if user_id is not None:
            await self._record(
                AnalysisRecord(
                    user_id=user_id,
                    kind=self.kind,
                    title=request.title,
                    language=ANALYZED_LANGUAGE,
                    code=code.value(),
                    complexity=self._notation(report),
                    complexity_class=self._complexity_class(report),
                    fingerprint=fingerprint.digest(),
                    duration_ms=round(duration_ms, 3),
                    cached=cached,
                    ai_explained=ai_report is not None,
                    report=_to_document(report),
                )
            )

        return AnalysisOutcome(report=report, ai=ai_report)

    def _get_report(
        self, code: NormalizedCode, fingerprint: Fingerprint
    ) -> tuple[ReportT, bool]:
        key, cached = self.process_cache(self.cache_namespace, fingerprint)
        if cached:
            return self._report_from_cache(cached), True

        report = self._analyze(code)
        self.cache_service.set_cache(key, report)
        return report, False

    async def _get_ai_report(self, fingerprint: Fingerprint, report: ReportT) -> AIReportT:
        key, cached = self.process_cache(self.ai_cache_namespace, fingerprint)
        if cached:
            return self._ai_report_from_cache(cached)

        ai_report = await self._explain(report)
        self.cache_service.set_cache(key, ai_report, ex_ttl=AI_CACHE_TTL_SECONDS)
        return ai_report

    async def _record(self, record: AnalysisRecord) -> None:
        # History is secondary: a failed write must never fail the analysis.
        # The recorder may block (mongoengine), so keep it off the event loop.
        try:
            await anyio.to_thread.run_sync(self.recorder.record, record)
        except Exception:
            logger.exception("Could not record %s analysis", self.kind.value)

    # ---- hooks -------------------------------------------------------------

    @abstractmethod
    def _analyze(self, code: NormalizedCode) -> ReportT: ...

    @abstractmethod
    def _report_from_cache(self, data: dict[str, Any]) -> ReportT: ...

    @abstractmethod
    def _ai_report_from_cache(self, data: dict[str, Any]) -> AIReportT: ...

    @abstractmethod
    async def _explain(self, report: ReportT) -> AIReportT: ...

    @abstractmethod
    def _notation(self, report: ReportT) -> str: ...

    @abstractmethod
    def _complexity_class(self, report: ReportT) -> ComplexityClass: ...


def _to_document(report: Any) -> dict[str, Any]:
    """Plain JSON-compatible dict (enums -> values, tuples -> lists)."""
    return json.loads(json.dumps(asdict(report)))
