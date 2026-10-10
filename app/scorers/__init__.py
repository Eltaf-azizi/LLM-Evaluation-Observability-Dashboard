"""Scorer registry. Add new scorers here and they're available everywhere."""
from .base import Score, Scorer
from .keyword import KeywordScorer
from .similarity import SimilarityScorer
from .llm_judge import LLMJudgeScorer

__all__ = [
    "Score", "Scorer",
    "KeywordScorer", "SimilarityScorer", "LLMJudgeScorer",
    "default_scorers",
]


def default_scorers(
    required_keywords: list[str] | None = None,
    reference: str = "",
    rubric: str = "The answer should be direct, correct, and helpful.",
) -> list:
    """One-stop factory used by smoke tests and the seed script."""
    return [
        KeywordScorer(required=required_keywords or []),
        SimilarityScorer(reference=reference or ""),
        LLMJudgeScorer(rubric=rubric),
    ]