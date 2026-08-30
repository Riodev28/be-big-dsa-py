"""Symbolic Big-O expressions.

A :class:`Complexity` is a sum of additive :class:`Term` monomials, e.g. ``n``,
``n²``, ``n log n``, ``n + m`` or ``2^n``. The cost engine builds these
bottom-up while walking the AST and renders the dominant form at the end.

Design rules encoded here:

* Sequential composition -> :meth:`Complexity.add` (Big-O max: keep the
  dominant term, keep terms that are incomparable such as ``n`` and ``m``).
* Nested composition -> :meth:`Complexity.multiply`.
* ``n + n² -> n²``, ``n + n log n -> n log n``, ``n + m -> n + m``.
"""

from __future__ import annotations

from dataclasses import dataclass

# Variable pool order; used to render products/sums in a stable, readable order.
_SYMBOL_ORDER = ("n", "m", "k", "p", "q", "r", "s", "t")

_SUPERSCRIPT = {1: "", 2: "²", 3: "³"}


def _symbol_rank(symbol: str) -> int:
    try:
        return _SYMBOL_ORDER.index(symbol)
    except ValueError:
        return len(_SYMBOL_ORDER)


def _render_power(symbol: str, exponent: int) -> str:
    if exponent in _SUPERSCRIPT:
        return f"{symbol}{_SUPERSCRIPT[exponent]}"
    return f"{symbol}^{exponent}"


@dataclass(frozen=True, slots=True)
class Term:
    """A single multiplicative monomial: symbols raised to exponents, an
    optional count of ``log n`` factors, or the exponential class ``2^n``
    (which subsumes any polynomial factor)."""

    powers: tuple[tuple[str, int], ...] = ()
    log: int = 0
    exponential: bool = False

    def __post_init__(self) -> None:
        if self.exponential:
            object.__setattr__(self, "powers", ())
            object.__setattr__(self, "log", 0)
            return

        merged: dict[str, int] = {}
        for symbol, exponent in self.powers:
            if exponent > 0:
                merged[symbol] = merged.get(symbol, 0) + exponent

        ordered = tuple(sorted(merged.items(), key=lambda item: _symbol_rank(item[0])))
        object.__setattr__(self, "powers", ordered)
        object.__setattr__(self, "log", max(self.log, 0))

    # -- introspection --------------------------------------------------

    @property
    def degree(self) -> int:
        """Total polynomial degree (sum of exponents)."""
        return sum(exponent for _, exponent in self.powers)

    def is_constant(self) -> bool:
        return not self.exponential and not self.powers and self.log == 0

    # -- algebra ------------------------------------------------------------

    def multiply(self, other: Term) -> Term:
        if self.exponential or other.exponential:
            return Term(exponential=True)
        return Term(tuple(self.powers) + tuple(other.powers), self.log + other.log)

    def with_extra_log(self) -> Term:
        if self.exponential:
            return self
        return Term(self.powers, self.log + 1)

    def dominates(self, other: Term) -> bool:
        """True when *self* makes *other* redundant inside a sum (Big-O max)."""
        if self.exponential != other.exponential:
            return self.exponential
        if self.exponential and other.exponential:
            return True

        mine = dict(self.powers)
        theirs = dict(other.powers)
        for symbol in mine.keys() | theirs.keys():
            if mine.get(symbol, 0) < theirs.get(symbol, 0):
                return False

        if self.degree != other.degree:
            return self.degree > other.degree
        return self.log >= other.log

    # -- rendering --------------------------------------------------------

    def render(self) -> str:
        if self.exponential:
            return "2^n"

        base = "·".join(_render_power(symbol, exp) for symbol, exp in self.powers)
        if self.log == 0:
            return base or "1"

        log_part = "log n" if self.log == 1 else f"log^{self.log} n"
        return f"{base} {log_part}" if base else log_part

    def sort_key(self) -> tuple:
        power_ranks = sorted(_symbol_rank(symbol) for symbol, _ in self.powers)
        return (
            int(self.exponential),
            self.degree,
            self.log,
            tuple(-rank for rank in power_ranks),
        )


_CONSTANT_TERM = Term()


@dataclass(frozen=True, slots=True)
class Complexity:
    """A sum of :class:`Term` monomials. A term set that is empty or holds only
    the constant term renders as ``O(1)``."""

    terms: frozenset[Term]

    # -- constructors -------------------------------------------------

    @classmethod
    def constant(cls) -> Complexity:
        return cls(frozenset({_CONSTANT_TERM}))

    @classmethod
    def linear(cls, symbol: str) -> Complexity:
        return cls(frozenset({Term(((symbol, 1),))}))

    @classmethod
    def power(cls, symbol: str, exponent: int) -> Complexity:
        if exponent <= 0:
            return cls.constant()
        return cls(frozenset({Term(((symbol, exponent),))}))

    @classmethod
    def logarithmic(cls) -> Complexity:
        return cls(frozenset({Term(log=1)}))

    @classmethod
    def exponential(cls) -> Complexity:
        return cls(frozenset({Term(exponential=True)}))

    # -- algebra ------------------------------------------------------------

    def add(self, other: Complexity) -> Complexity:
        if not self.terms:
            return other
        if not other.terms:
            return self
        return Complexity(_dominant(self.terms | other.terms))

    def multiply(self, other: Complexity) -> Complexity:
        if not self.terms or not other.terms:
            return Complexity(frozenset())
        products = {
            left.multiply(right) for left in self.terms for right in other.terms
        }
        return Complexity(_dominant(frozenset(products)))

    def times_log(self) -> Complexity:
        return Complexity(frozenset(term.with_extra_log() for term in self.terms))

    # -- introspection --------------------------------------------------

    def is_constant(self) -> bool:
        return all(term.is_constant() for term in self.terms)

    def is_exponential(self) -> bool:
        return any(term.exponential for term in self.terms)

    def has_log(self) -> bool:
        return any(term.log > 0 for term in self.terms)

    def max_degree(self) -> int:
        return max((term.degree for term in self.terms), default=0)

    # -- rendering --------------------------------------------------------

    def _ordered_terms(self) -> list[Term]:
        return sorted(self.terms, key=Term.sort_key, reverse=True)

    def render(self) -> str:
        if self.is_constant():
            return "O(1)"
        return f"O({' + '.join(term.render() for term in self._ordered_terms())})"

    def term_strings(self) -> tuple[str, ...]:
        if self.is_constant():
            return ("1",)
        return tuple(term.render() for term in self._ordered_terms())


def _dominant(terms: frozenset[Term]) -> frozenset[Term]:
    """Drop every term that another term in the set strictly dominates."""
    return frozenset(
        term
        for term in terms
        if not any(other != term and other.dominates(term) for other in terms)
    )
