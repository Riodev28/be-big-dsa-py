"""Pure metric math: no database, no HTTP, no clock.

Everything here takes plain values and returns plain values, so the rules
behind each dashboard number are unit-testable in isolation.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.shared.ast.complexity import ComplexityClass


@dataclass(frozen=True)
class NotationCount:
    notation: str
    complexity_class: ComplexityClass
    count: int


@dataclass(frozen=True)
class Mode:
    notation: str
    complexity_class: ComplexityClass
    occurrences: int
    share_pct: float


Month = tuple[int, int]  # (year, month)


def health_score(class_counts: Iterable[tuple[ComplexityClass, int]]) -> float | None:
    """Count-weighted average of each class's health score, 0..100."""
    total = weighted = 0
    for complexity_class, count in class_counts:
        total += count
        weighted += complexity_class.health_score * count
    return round(weighted / total, 1) if total else None


def mode(counts: Iterable[NotationCount]) -> Mode | None:
    """Most frequent notation. Ties go to the cheaper class, then alphabetically,
    so the answer is stable between requests."""
    counts = list(counts)
    if not counts:
        return None

    total = sum(c.count for c in counts)
    top = min(counts, key=lambda c: (-c.count, c.complexity_class.rank, c.notation))
    return Mode(
        notation=top.notation,
        complexity_class=top.complexity_class,
        occurrences=top.count,
        share_pct=round(top.count / total * 100, 1),
    )


def percent_change(current: int, previous: int) -> float | None:
    """None when there is no previous value: growth from zero is undefined,
    and showing "+100%" or "+inf%" would be misleading."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def last_months(now: datetime, count: int) -> list[Month]:
    """The `count` calendar months ending with `now`'s month, oldest first."""
    months = []
    year, month = now.year, now.month
    for _ in range(count):
        months.append((year, month))
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return months[::-1]


def month_start(month: Month, tzinfo=None) -> datetime:
    return datetime(month[0], month[1], 1, tzinfo=tzinfo)


def format_month(month: Month) -> str:
    return f"{month[0]:04d}-{month[1]:02d}"
