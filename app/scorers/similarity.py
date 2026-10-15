"""Similarity scorer: cosine similarity between output and a reference answer.

Bag-of-words (token counts) — no ML, no dependencies, fully deterministic.
For semantic similarity, swap `_vectorize` for an embeddings call (see note).
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .base import Score

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _vectorize(text: str) -> Counter:
    """Lowercase, split on non-alphanumerics, return token counts."""
    return Counter(_TOKEN_RE.findall(text.lower()))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SimilarityScorer:
    name = "similarity"

    def __init__(self, reference: str, ignore: list[str] | None = None) -> None:
        """`reference` is the gold-standard answer you compare against.
        `ignore` is an optional stopword list (e.g. ['the', 'a', 'is']).
        """
        self.reference = reference
        self.ignore = set(ignore or [])

    def _clean(self, text: str) -> Counter:
        vec = _vectorize(text)
        for w in self.ignore:
            vec.pop(w, None)
        return vec

    def score(self, prompt: str, output: str) -> Score:
        a = self._clean(output)
        b = self._clean(self.reference)
        sim = _cosine(a, b)
        return Score(
            name=self.name,
            value=sim,
            details={
                "reference_excerpt": self.reference[:120],
                "output_excerpt": output[:120],
                "overlap_terms": sorted(set(a) & set(b))[:20],
            },
        )