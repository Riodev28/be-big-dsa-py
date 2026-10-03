from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.shared.analysis import AnalysisKind
from app.shared.ast.complexity import ComplexityClass, Severity
from app.shared.types import ObjectIdStr


class ComplexityClassInfo(BaseModel):
    key: ComplexityClass
    label: str
    severity: Severity

    @classmethod
    def of(cls, complexity_class: ComplexityClass | str) -> "ComplexityClassInfo":
        complexity_class = ComplexityClass(complexity_class)
        return cls(
            key=complexity_class,
            label=complexity_class.label,
            severity=complexity_class.severity,
        )


# ---- dashboard -------------------------------------------------------------


class TotalAnalysesMetric(BaseModel):
    value: int
    this_week: int
    last_week: int
    change_vs_last_week_pct: float | None


class ModeComplexityMetric(BaseModel):
    notation: str
    complexity_class: ComplexityClassInfo
    occurrences: int
    share_pct: float


class DashboardSummaryResponse(BaseModel):
    kind: AnalysisKind
    total_analyses: TotalAnalysesMetric
    mode_complexity: ModeComplexityMetric | None
    average_analysis_time_ms: float | None
    code_health_score: float | None


class TrendPoint(BaseModel):
    month: str  # "YYYY-MM"
    current: float | None  # None = no analyses that month, not a score of 0
    baseline: float | None


class ComplexityTrendsResponse(BaseModel):
    kind: AnalysisKind
    metric: Literal["code_health_score"] = "code_health_score"
    points: list[TrendPoint]


# ---- history ---------------------------------------------------------------


class AnalysisListItem(BaseModel):
    id: ObjectIdStr
    title: str | None
    kind: AnalysisKind
    complexity: str
    complexity_class: ComplexityClassInfo
    language: str
    created_at: datetime

    @classmethod
    def from_model(cls, record) -> "AnalysisListItem":
        return cls(**cls._common_fields(record))

    @staticmethod
    def _common_fields(record) -> dict[str, Any]:
        return {
            "id": record.id,
            "title": record.title,
            "kind": record.kind,
            "complexity": record.complexity,
            "complexity_class": ComplexityClassInfo.of(record.complexity_class),
            "language": record.language,
            "created_at": record.created_at,
        }


class AnalysisPage(BaseModel):
    items: list[AnalysisListItem]
    total: int
    limit: int
    offset: int


class AnalysisDetailResponse(AnalysisListItem):
    code: str
    report: dict[str, Any]
    duration_ms: float
    cached: bool
    ai_explained: bool

    @classmethod
    def from_model(cls, record) -> "AnalysisDetailResponse":
        return cls(
            **cls._common_fields(record),
            code=record.code,
            report=record.report,
            duration_ms=record.duration_ms,
            cached=record.cached,
            ai_explained=record.ai_explained,
        )
