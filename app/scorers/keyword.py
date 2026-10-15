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

    