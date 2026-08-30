from dataclasses import dataclass
from typing import Any

from app.shared.ast.complexity import VariableRef


def _as_variable_ref(item: Any) -> VariableRef:
    if isinstance(item, VariableRef):
        return item
    if isinstance(item, dict):
        return VariableRef(**item)
    return VariableRef(*item)


@dataclass(frozen=True, slots=True)
class TemporalAnalysisReport:
    time_complexity: str
    max_loop_depth: int
    recursive: bool
    terms: tuple[str, ...]
    variables: tuple[VariableRef, ...]
    loop_count: int
    recursion_kind: str | None

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> "TemporalAnalysisReport":
        """Rebuild a report from its cached JSON form (see CacheService)."""
        return cls(
            time_complexity=data["time_complexity"],
            max_loop_depth=data["max_loop_depth"],
            recursive=data["recursive"],
            terms=tuple(data.get("terms", ())),
            variables=tuple(
                _as_variable_ref(item) for item in data.get("variables", ())
            ),
            loop_count=data.get("loop_count", 0),
            recursion_kind=data.get("recursion_kind"),
        )
