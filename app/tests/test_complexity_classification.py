import textwrap

import pytest

from app.features.temporal_complexity import TemporalComplexityAnalyzer
from app.shared.ast import NormalizedCode
from app.shared.ast.complexity import ComplexityClass, Severity


def classify_code(code: str) -> ComplexityClass:
    report = TemporalComplexityAnalyzer(NormalizedCode(textwrap.dedent(code))).analyze()
    return report.complexity_class


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("x = 1\n", ComplexityClass.CONSTANT),
        ("for i in range(n):\n    pass\n", ComplexityClass.LINEAR),
        (
            "for a in xs:\n    pass\nfor b in ys:\n    pass\n",
            ComplexityClass.LINEAR,  # O(n + m): independent inputs, still linear
        ),
        ("xs.sort()\n", ComplexityClass.LINEARITHMIC),
        (
            "for i in range(n):\n    for j in range(n):\n        pass\n",
            ComplexityClass.QUADRATIC,
        ),
        (
            "for i in range(n):\n    for j in range(n):\n        for k in range(n):\n            pass\n",
            ComplexityClass.CUBIC,
        ),
        (
            "def fib(n):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)\n",
            ComplexityClass.EXPONENTIAL,
        ),
    ],
)
def test_analyzer_reports_complexity_class(code, expected):
    assert classify_code(code) == expected


def test_classes_are_ordered_and_scores_never_increase():
    classes = list(ComplexityClass)
    assert [c.rank for c in classes] == list(range(len(classes)))
    scores = [c.health_score for c in classes]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize(
    ("complexity_class", "severity"),
    [
        (ComplexityClass.LINEARITHMIC, Severity.GOOD),
        (ComplexityClass.QUADRATIC, Severity.WARNING),
        (ComplexityClass.CUBIC, Severity.WARNING),
        (ComplexityClass.EXPONENTIAL, Severity.CRITICAL),
    ],
)
def test_severity_bands(complexity_class, severity):
    assert complexity_class.severity == severity
