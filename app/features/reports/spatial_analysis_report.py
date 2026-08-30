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
class SpatialAnalysisReport:
    space_complexity: str

    total_allocations: int

    list_allocations: int
    dict_allocations: int
    set_allocations: int

    comprehensions: int

    recursive_functions: int

    generator_expressions: int

    dynamic_growth_operations: int

    terms: tuple[str, ...] = ()
    variables: tuple[VariableRef, ...] = ()
    recursion_kind: str | None = None

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> "SpatialAnalysisReport":
        """Rebuild a report from its cached JSON form (see CacheService)."""
        return cls(
            space_complexity=data["space_complexity"],
            total_allocations=data["total_allocations"],
            list_allocations=data["list_allocations"],
            dict_allocations=data["dict_allocations"],
            set_allocations=data["set_allocations"],
            comprehensions=data["comprehensions"],
            recursive_functions=data["recursive_functions"],
            generator_expressions=data["generator_expressions"],
            dynamic_growth_operations=data["dynamic_growth_operations"],
            terms=tuple(data.get("terms", ())),
            variables=tuple(
                _as_variable_ref(item) for item in data.get("variables", ())
            ),
            recursion_kind=data.get("recursion_kind"),
        )
