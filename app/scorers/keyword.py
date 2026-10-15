"""Keyword / regex scorer.

Score = fraction of required keywords that appear in the output.
Case-insensitive by default. Optional `banned` list: any banned word caps
the score at 0.0 (useful for hallucination / safety checks).
"""
from __future__ import annotations

import re

from .base import Score


class KeywordScorer:
    name = "keyword"

    def __init__(
        self,
        required: list[str] | None = None,
        banned: list[str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        self.required = required or []
        self.banned = banned or []
        self.case_sensitive = case_sensitive

    def _find(self, needle: str, haystack: str) -> bool:
        if self.case_sensitive:
            return needle in haystack
        return needle.lower() in haystack.lower()

    def score(self, prompt: str, output: str) -> Score:
        found = [k for k in self.required if self._find(k, output)]
        missing = [k for k in self.required if k not in found]
        hit_banned = [b for b in self.banned if self._find(b, output)]

        # Base score: coverage of required keywords
        base = len(found) / len(self.required) if self.required else 1.0

        # Any banned word => 0.0 (a hard fail)
        value = 0.0 if hit_banned else base

        return Score(
            name=self.name,
            value=value,
            details={
                "found": found,
                "missing": missing,
                "banned_hits": hit_banned,
                "coverage": base,
            },
        )