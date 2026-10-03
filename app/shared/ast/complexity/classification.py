"""Growth classes: a coarse, ordered bucket for any :class:`Complexity`.

The rendered notation (``O(n log n)``, ``O(n + m)`` ...) is open-ended, so it
can't be aggregated or scored directly. Every expression is mapped to one of
these classes by its dominant term, and everything downstream (health score,
badges, charts) reads the class instead of parsing strings.
"""

from __future__ import annotations

from enum import Enum

from .expression import Complexity


class Severity(str, Enum):
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


class ComplexityClass(str, Enum):
    # Declared from cheapest to most expensive growth: `rank` relies on it
    CONSTANT = "constant"
    LOGARITHMIC = "logarithmic"
    LINEAR = "linear"
    LINEARITHMIC = "linearithmic"
    QUADRATIC = "quadratic"
    CUBIC = "cubic"
    POLYNOMIAL = "polynomial"
    EXPONENTIAL = "exponential"

    @property
    def rank(self) -> int:
        """0 = cheapest growth. Lets callers sort/compare classes."""
        return _ORDER.index(self)

    @property
    def label(self) -> str:
        return self.value.capitalize()

    @property
    def health_score(self) -> float:
        """How healthy code of this class is, from 0 to 100."""
        return _HEALTH_SCORES[self]

    @property
    def severity(self) -> Severity:
        if self.rank <= ComplexityClass.LINEARITHMIC.rank:
            return Severity.GOOD
        if self.rank <= ComplexityClass.CUBIC.rank:
            return Severity.WARNING
        return Severity.CRITICAL


_ORDER = list(ComplexityClass)

# Single source of truth for the health policy. Changing a number here
# re-scores all history, because records store the class, not the score.
_HEALTH_SCORES: dict[ComplexityClass, float] = {
    ComplexityClass.CONSTANT: 100,
    ComplexityClass.LOGARITHMIC: 95,
    ComplexityClass.LINEAR: 85,
    ComplexityClass.LINEARITHMIC: 75,
    ComplexityClass.QUADRATIC: 45,
    ComplexityClass.CUBIC: 25,
    ComplexityClass.POLYNOMIAL: 10,
    ComplexityClass.EXPONENTIAL: 0,
}

_BY_DEGREE = {
    2: ComplexityClass.QUADRATIC,
    3: ComplexityClass.CUBIC,
}


def classify(complexity: Complexity) -> ComplexityClass:
    """Bucket an expression by its worst term.

    Multi-variable terms count total degree: ``n + m`` is linear,
    ``n·m`` is quadratic. A log factor only matters below degree 2.
    """
    if complexity.is_exponential():
        return ComplexityClass.EXPONENTIAL
    if complexity.is_constant():
        return ComplexityClass.CONSTANT

    degree = complexity.max_degree()
    if degree == 0:
        return ComplexityClass.LOGARITHMIC
    if degree == 1:
        has_log = any(t.degree == 1 and t.log > 0 for t in complexity.terms)
        return ComplexityClass.LINEARITHMIC if has_log else ComplexityClass.LINEAR
    return _BY_DEGREE.get(degree, ComplexityClass.POLYNOMIAL)
