"""Allocation of Big-O variable names (``n``, ``m``, ``k``, …) to the distinct
things a program iterates over."""

from __future__ import annotations

from dataclasses import dataclass

_POOL = ("n", "m", "k", "p", "q", "r", "s", "t")


@dataclass(frozen=True, slots=True)
class VariableRef:
    """A resolved Big-O variable and the source expression it stands for."""

    symbol: str
    source: str


class SymbolRegistry:
    """Maps a *source key* (a normalized string describing a loop's iterable) to
    a stable variable name. The same key always yields the same symbol, so two
    loops over the same collection share a variable and two loops over different
    collections get ``n`` and ``m``."""

    def __init__(self) -> None:
        self._by_key: dict[str, str] = {}

    def symbol_for(self, key: str) -> str:
        if key not in self._by_key:
            index = len(self._by_key)
            self._by_key[key] = _POOL[index] if index < len(_POOL) else f"n{index + 1}"
        return self._by_key[key]

    def variables(self) -> tuple[VariableRef, ...]:
        return tuple(
            VariableRef(symbol=symbol, source=key)
            for key, symbol in self._by_key.items()
        )
