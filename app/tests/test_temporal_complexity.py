"""End-to-end tests for the temporal (time) complexity analyzer.

Each case feeds a Python snippet through the real pipeline
(``NormalizedCode`` -> ``TemporalComplexityAnalyzer``) and asserts the inferred
Big-O string.
"""

import textwrap

import pytest

from app.features.temporal_complexity.analyzer import TemporalComplexityAnalyzer
from app.shared.ast.value_objects import NormalizedCode


def analyze(code: str):
    return TemporalComplexityAnalyzer(NormalizedCode(textwrap.dedent(code))).analyze()


def complexity(code: str) -> str:
    return analyze(code).time_complexity


CASES = {
    "no-loops": ("x = 1\ny = x + 2\n", "O(1)"),
    "single-loop": ("for i in range(n):\n    total += i\n", "O(n)"),
    "sequential-same-source": (
        "for x in data:\n    a(x)\nfor x in data:\n    b(x)\n",
        "O(n)",
    ),
    "sequential-different-sources": (
        "for a in xs:\n    pass\nfor b in ys:\n    pass\n",
        "O(n + m)",
    ),
    "nested-same-range": (
        "for i in range(n):\n    for j in range(n):\n        pass\n",
        "O(n²)",
    ),
    "nested-different-range-collapses": (
        "for i in range(n):\n    for j in range(m):\n        pass\n",
        "O(n²)",
    ),
    "triple-nested": (
        "for i in range(n):\n    for j in range(n):\n        for k in range(n):\n            pass\n",
        "O(n³)",
    ),
    "nested-then-sequential": (
        "for i in range(a):\n    for j in range(a):\n        pass\nfor k in range(b):\n    pass\n",
        "O(n² + m)",
    ),
    "constant-bound-loop": ("for _ in range(10):\n    print(_)\n", "O(1)"),
    "sorted-call": ("result = sorted(arr)\n", "O(n log n)"),
    "sort-method": ("arr.sort()\n", "O(n log n)"),
    "sorted-in-loop-header": ("for x in sorted(arr):\n    print(x)\n", "O(n log n)"),
    "membership-in-unknown-name-is-linear": (
        "for i in range(n):\n    if i in items:\n        return i\n",
        "O(n²)",
    ),
    "membership-in-dict-is-constant": (
        """
        seen = {}
        for i, x in enumerate(nums):
            if x in seen:
                return i
            seen[x] = i
        """,
        "O(n)",
    ),
    "membership-in-set-is-constant": (
        """
        seen = set()
        for i in range(n):
            if i in seen:
                return i
            seen.add(i)
        """,
        "O(n)",
    ),
    "two-sequential-loops-with-dict-lookups": (
        """
        def two_sum(a, b, target):
            table = {}
            for i, v in enumerate(a):
                if target - v in table:
                    return i
                table[v] = i
            for i, v in enumerate(b):
                if target - v in table:
                    return i
                table[v] = i
        """,
        "O(n + m)",
    ),
    "nested-comprehension": ("flat = [y for row in grid for y in row]\n", "O(n²)"),
    "iterative-binary-search": (
        """
        lo, hi = 0, len(arr) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid] == target:
                break
            elif arr[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        """,
        "O(log n)",
    ),
    "recursive-binary-search": (
        """
        def bs(arr, lo, hi, target):
            if lo > hi:
                return -1
            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                return bs(arr, mid + 1, hi, target)
            else:
                return bs(arr, lo, mid - 1, target)
        """,
        "O(log n)",
    ),
    "linear-recursion": (
        """
        def fact(n):
            if n <= 1:
                return 1
            return n * fact(n - 1)
        """,
        "O(n)",
    ),
    "merge-sort": (
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
        "O(n log n)",
    ),
    "naive-fibonacci": (
        """
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
        """,
        "O(2^n)",
    ),
    "leetcode-style-class": (
        """
        class Solution:
            def two_sum(self, nums, target):
                for i in range(len(nums)):
                    for j in range(i + 1, len(nums)):
                        if nums[i] + nums[j] == target:
                            return [i, j]
        """,
        "O(n²)",
    ),
    "function-with-loop-called-in-loop": (
        """
        def scan(items):
            for item in items:
                use(item)

        for row in matrix:
            scan(row)
        """,
        "O(n²)",
    ),
}


@pytest.mark.parametrize(
    ("code", "expected"), list(CASES.values()), ids=list(CASES.keys())
)
def test_time_complexity(code, expected):
    assert complexity(code) == expected


def test_sequential_loops_expose_two_variables():
    report = analyze("for a in xs:\n    pass\nfor b in ys:\n    pass\n")
    assert report.terms == ("n", "m")
    assert {v.symbol for v in report.variables} == {"n", "m"}
    assert {v.source for v in report.variables} == {"xs", "ys"}


def test_report_carries_loop_metrics():
    report = analyze("for i in range(n):\n    for j in range(n):\n        pass\n")
    assert report.max_loop_depth == 2
    assert report.loop_count == 2
    assert report.recursive is False
    assert report.recursion_kind is None


def test_recursion_kind_is_reported():
    report = analyze(
        "def fib(n):\n"
        "    if n < 2:\n        return n\n"
        "    return fib(n - 1) + fib(n - 2)\n"
    )
    assert report.recursive is True
    assert report.recursion_kind == "exponential"


def test_report_survives_cache_round_trip():
    import json

    from app.features.reports import TemporalAnalysisReport
    from app.shared.cache.service import CacheService

    report = analyze(
        "for i in range(a):\n    for j in range(a):\n        pass\nfor k in range(b):\n    pass\n"
    )
    blob = json.dumps(CacheService._serialize(report))
    restored = TemporalAnalysisReport.from_cache(json.loads(blob))
    assert restored == report
