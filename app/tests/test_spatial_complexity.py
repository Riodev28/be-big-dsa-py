"""End-to-end tests for the spatial (space) complexity analyzer."""

import textwrap

import pytest

from app.features.spatial_complexity.analyzer import SpatialComplexityAnalyzer
from app.shared.ast.value_objects import NormalizedCode


def analyze(code: str):
    return SpatialComplexityAnalyzer(NormalizedCode(textwrap.dedent(code))).analyze()


def space(code: str) -> str:
    return analyze(code).space_complexity


CASES = {
    "scalars-only": ("x = 1\ny = x + 2\nx, y = y, x\n", "O(1)"),
    "fixed-size-structures": ("pair = [a, b]\ntable = {}\n", "O(1)"),
    "swap-in-place": ("def rev(a):\n    a[0], a[-1] = a[-1], a[0]\n", "O(1)"),
    "generator-is-lazy": ("total = sum(v * v for v in data)\n", "O(1)"),
    "list-comprehension": ("out = [v * 2 for v in data]\n", "O(n)"),
    "list-times-int": ("row = [0] * n\n", "O(n)"),
    "slice-copy": ("half = arr[: len(arr) // 2]\n", "O(n)"),
    "sorted-copy": ("s = sorted(arr)\n", "O(n)"),
    "grow-list-in-loop": (
        "res = []\nfor x in data:\n    res.append(x * x)\n",
        "O(n)",
    ),
    "grow-dict-in-loop": (
        "seen = {}\nfor i, x in enumerate(nums):\n    seen[x] = i\n",
        "O(n)",
    ),
    "grow-set-in-loop": (
        "seen = set()\nfor x in data:\n    seen.add(x)\n",
        "O(n)",
    ),
    "transient-list-not-scaled": (
        "for i in range(n):\n    tmp = [0] * n\n    consume(tmp)\n",
        "O(n)",
    ),
    "transient-scalar-list": (
        "for x in data:\n    pair = [x, x + 1]\n    consume(pair)\n",
        "O(1)",
    ),
    "grid-append-in-nested-loop": (
        """
        pairs = []
        for i in range(n):
            for j in range(n):
                pairs.append((i, j))
        """,
        "O(n²)",
    ),
    "grid-of-rows": (
        """
        grid = []
        for i in range(n):
            row = [0] * n
            grid.append(row)
        """,
        "O(n²)",
    ),
    "two-dimensional-comprehension": (
        "grid = [[0] * n for _ in range(m)]\n",
        "O(n²)",
    ),
    "two-independent-structures": (
        """
        a_set = set()
        for x in xs:
            a_set.add(x)
        b_list = []
        for y in ys:
            b_list.append(y)
        """,
        "O(n + m)",
    ),
    "recursive-binary-search-stack": (
        """
        def bs(arr, lo, hi, t):
            if lo > hi:
                return -1
            mid = (lo + hi) // 2
            if arr[mid] == t:
                return mid
            if arr[mid] < t:
                return bs(arr, mid + 1, hi, t)
            return bs(arr, lo, mid - 1, t)
        """,
        "O(log n)",
    ),
    "linear-recursion-stack": (
        "def f(n):\n    if n <= 0:\n        return 0\n    return n + f(n - 1)\n",
        "O(n)",
    ),
    "tree-recursion-stack-is-linear": (
        """
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
        """,
        "O(n)",
    ),
    "merge-sort-space": (
        """
        def merge_sort(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = merge_sort(arr[:mid])
            right = merge_sort(arr[mid:])
            out = []
            i = j = 0
            while i < len(left) and j < len(right):
                if left[i] < right[j]:
                    out.append(left[i])
                    i += 1
                else:
                    out.append(right[j])
                    j += 1
            return out + left[i:] + right[j:]
        """,
        "O(n)",
    ),
    "hashmap-two-sum-is-linear": (
        """
        def two_sum(nums, target):
            seen = {}
            for i, x in enumerate(nums):
                if target - x in seen:
                    return [seen[target - x], i]
                seen[x] = i
        """,
        "O(n)",
    ),
}


@pytest.mark.parametrize(
    ("code", "expected"), list(CASES.values()), ids=list(CASES.keys())
)
def test_space_complexity(code, expected):
    assert space(code) == expected


def test_two_structures_expose_two_variables():
    report = analyze(
        "a = []\nfor x in xs:\n    a.append(x)\nb = set()\nfor y in ys:\n    b.add(y)\n"
    )
    assert report.terms == ("n", "m")
    assert {v.source for v in report.variables} == {"xs", "ys"}


def test_recursion_kind_reported():
    report = analyze(
        "def f(n):\n    if n <= 0:\n        return 0\n    return n + f(n - 1)\n"
    )
    assert report.recursive_functions == 1
    assert report.recursion_kind == "linear"


def test_report_survives_cache_round_trip():
    import json

    from app.features.reports import SpatialAnalysisReport
    from app.shared.cache.service import CacheService

    report = analyze(
        "grid = []\nfor i in range(n):\n    row = [0] * n\n    grid.append(row)\n"
    )
    blob = json.dumps(CacheService._serialize(report))
    restored = SpatialAnalysisReport.from_cache(json.loads(blob))
    assert restored == report
