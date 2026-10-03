"""Port for persisting finished analyses.

The analysis services only know this interface; the MongoDB adapter lives in
the analytics feature. That keeps `shared` free of feature imports and lets
tests (or anonymous requests) plug in the no-op recorder.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from app.shared.ast.complexity import ComplexityClass


class AnalysisKind(str, Enum):
    TEMPORAL = "temporal"
    SPATIAL = "spatial"


@dataclass(frozen=True)
class AnalysisRecord:
    user_id: str
    kind: AnalysisKind
    title: str | None
    language: str
    code: str
    complexity: str
    complexity_class: ComplexityClass
    fingerprint: str
    duration_ms: float
    cached: bool
    ai_explained: bool
    report: dict[str, Any]


class AnalysisRecorder(Protocol):
    def record(self, record: AnalysisRecord) -> None: ...


class NullAnalysisRecorder:
    """Null Object: records nothing, so callers never need `if recorder:`."""

    def record(self, record: AnalysisRecord) -> None:
        pass
