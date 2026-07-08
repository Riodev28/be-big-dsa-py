from dataclasses import dataclass


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
