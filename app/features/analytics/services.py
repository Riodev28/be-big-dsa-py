from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.shared.analysis import AnalysisKind
from app.shared.helpers.datetime_helper import utcnow

from . import metrics
from .exceptions import AnalyticsExceptions
from .repository import AnalysisRecordRepository
from .schemas import (
    AnalysisDetailResponse,
    AnalysisListItem,
    AnalysisPage,
    ComplexityClassInfo,
    ComplexityTrendsResponse,
    DashboardSummaryResponse,
    ModeComplexityMetric,
    TotalAnalysesMetric,
    TrendPoint,
)

WEEK = timedelta(days=7)

Clock = Callable[[], datetime]


class DashboardService:
    """
    Read side: turns history into the dashboard numbers. Fetching is the
    repository's job, the math is in `metrics`; this class only composes
    them. The clock is injected so "this week" is deterministic in tests.
    """

    def __init__(self, repository: AnalysisRecordRepository, clock: Clock = utcnow):
        self.repository = repository
        self.clock = clock

    def summary(self, user_id: str, kind: AnalysisKind) -> DashboardSummaryResponse:
        notation_counts = self.repository.latest_notation_counts(user_id, kind)
        mode = metrics.mode(notation_counts)
        avg_ms = self.repository.average_duration_ms(user_id, kind)

        return DashboardSummaryResponse(
            kind=kind,
            total_analyses=self._total_analyses(user_id, kind),
            mode_complexity=self._mode_metric(mode),
            average_analysis_time_ms=round(avg_ms, 1) if avg_ms is not None else None,
            code_health_score=metrics.health_score(
                (c.complexity_class, c.count) for c in notation_counts
            ),
        )

    def trends(self, user_id: str, kind: AnalysisKind, months: int) -> ComplexityTrendsResponse:
        window = metrics.last_months(self.clock(), months)
        since = metrics.month_start(window[0], tzinfo=timezone.utc)

        current = self.repository.monthly_class_counts(kind, since, user_id=user_id)
        baseline = self.repository.monthly_class_counts(kind, since)

        return ComplexityTrendsResponse(
            kind=kind,
            points=[
                TrendPoint(
                    month=metrics.format_month(month),
                    current=metrics.health_score(current.get(month, [])),
                    baseline=metrics.health_score(baseline.get(month, [])),
                )
                for month in window
            ],
        )

    def _total_analyses(self, user_id: str, kind: AnalysisKind) -> TotalAnalysesMetric:
        now = self.clock()
        this_week = self.repository.count(user_id, kind, since=now - WEEK)
        last_week = self.repository.count(user_id, kind, since=now - 2 * WEEK, until=now - WEEK)

        return TotalAnalysesMetric(
            value=self.repository.count(user_id, kind),
            this_week=this_week,
            last_week=last_week,
            change_vs_last_week_pct=metrics.percent_change(this_week, last_week),
        )

    @staticmethod
    def _mode_metric(mode: metrics.Mode | None) -> ModeComplexityMetric | None:
        if mode is None:
            return None
        return ModeComplexityMetric(
            notation=mode.notation,
            complexity_class=ComplexityClassInfo.of(mode.complexity_class),
            occurrences=mode.occurrences,
            share_pct=mode.share_pct,
        )


class AnalysisHistoryService:
    """Browsing a user's past analyses ("Recent reports" / "View all")."""

    def __init__(self, repository: AnalysisRecordRepository):
        self.repository = repository

    def list_page(
        self, user_id: str, kind: AnalysisKind | None, limit: int, offset: int
    ) -> AnalysisPage:
        records, total = self.repository.list_page(user_id, kind, limit, offset)
        return AnalysisPage(
            items=[AnalysisListItem.from_model(r) for r in records],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, id: str, user_id: str) -> AnalysisDetailResponse:
        record = self.repository.get(id, user_id)
        if record is None:
            raise AnalyticsExceptions.not_found()
        return AnalysisDetailResponse.from_model(record)
