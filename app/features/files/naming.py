"""Automatic algorithm names for files.

`FileService` depends on the `AlgorithmNamer` port; the AI adapter lives here
too because nothing else needs it. Naming is a nice-to-have: if the AI fails,
the file is still saved, just without a name.
"""

import logging
from typing import Protocol

from app.shared.ai.service import AIService

logger = logging.getLogger(__name__)

MAX_ALGORITHM_NAME_LENGTH = 100
_UNKNOWN_ANSWERS = {"unknown", "none", "n/a", ""}


class AlgorithmNamer(Protocol):
    def name(self, code: str) -> str | None: ...


class NullAlgorithmNamer:
    """Null Object: names nothing, so callers never need `if namer:`."""

    def name(self, code: str) -> str | None:
        return None


class AIAlgorithmNamer:
    def __init__(self, ai: AIService):
        self.ai = ai

    def name(self, code: str) -> str | None:
        if not code.strip():
            return None
        try:
            return clean_algorithm_name(self.ai.identify_algorithm(code))
        except Exception:
            logger.exception("Could not generate an algorithm name")
            return None


def clean_algorithm_name(raw: str) -> str | None:
    """Model output -> a short single-line name, or None when it didn't know."""
    lines = raw.strip().splitlines()
    name = lines[0] if lines else ""
    name = name.strip().strip("\"'`*").rstrip(".").strip()
    if name.lower() in _UNKNOWN_ANSWERS:
        return None
    return name[:MAX_ALGORITHM_NAME_LENGTH]
