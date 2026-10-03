from datetime import datetime

from app.features.analytics import metrics
from app.features.analytics.metrics import NotationCount
from app.shared.ast.complexity import ComplexityClass as C


def test_health_score_is_count_weighted():
    # 3 x linear (85) + 1 x quadratic (45) = 300 / 4
    assert metrics.health_score([(C.LINEAR, 3), (C.QUADRATIC, 1)]) == 75.0


def test_health_score_without_data_is_none_not_zero():
    assert metrics.health_score([]) is None


def test_mode_picks_most_frequent_and_reports_share():
    result = metrics.mode(
        [
            NotationCount("O(n)", C.LINEAR, 1),
            NotationCount("O(n log n)", C.LINEARITHMIC, 3),
        ]
    )
    assert result.notation == "O(n log n)"
    assert result.occurrences == 3
    assert result.share_pct == 75.0


def test_mode_tie_prefers_cheaper_class():
    result = metrics.mode(
        [
            NotationCount("O(n²)", C.QUADRATIC, 2),
            NotationCount("O(n)", C.LINEAR, 2),
        ]
    )
    assert result.notation == "O(n)"


def test_mode_empty():
    assert metrics.mode([]) is None


def test_percent_change():
    assert metrics.percent_change(112, 100) == 12.0
    assert metrics.percent_change(50, 100) == -50.0
    assert metrics.percent_change(5, 0) is None


def test_last_months_crosses_year_boundary():
    assert metrics.last_months(datetime(2026, 2, 15), 4) == [
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
    ]


def test_format_month():
    assert metrics.format_month((2026, 7)) == "2026-07"
