"""The Scorer contract.

Any object with `.name` (str) and `.score(prompt, output) -> Score` is a scorer.
We don't use ABCs here — duck typing is enough and keeps new scorers tiny.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Score:
    """One scorer's verdict on one (prompt, output) pair.

    value is ALWAYS clamped to [0.0, 1.0] so scores from different scorers
    are comparable on the same chart.
    """
    name: str
    value: float
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defensive clamp — a buggy scorer shouldn't corrupt the dashboard.
        if self.value < 0.0:
            self.value = 0.0
        elif self.value > 1.0:
            self.value = 1.0


class Scorer(Protocol):
    name: str
    def score(self, prompt: str, output: str) -> Score: ...