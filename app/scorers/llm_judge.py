"""LLM-as-judge scorer.

Sends (prompt, output, rubric) to the same LLMClient used for the main call
and asks for a structured JSON verdict. Falls back gracefully on parse errors.
"""
from __future__ import annotations

import json
import re

from ..llm import LLMClient
from .base import Score

# The [[JUDGE_JSON]] sentinel lets the mock client know to return JSON,
# so the whole pipeline is testable offline.
JUDGE_TEMPLATE = """[[JUDGE_JSON]]
You are a strict evaluator. Score the model output against the rubric.

RUBRIC: {rubric}

USER PROMPT:
{prompt}

MODEL OUTPUT:
{output}

Return ONLY compact JSON in this exact shape:
{{"score": <integer 0-10>, "reason": "<one short sentence>"}}
"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class LLMJudgeScorer:
    name = "llm_judge"

    def __init__(self, rubric: str, client: LLMClient | None = None) -> None:
        self.rubric = rubric
        self.client = client or LLMClient()

    def score(self, prompt: str, output: str) -> Score:
        judge_prompt = JUDGE_TEMPLATE.format(
            rubric=self.rubric, prompt=prompt, output=output
        )
        result = self.client.complete(judge_prompt, temperature=0.0)

        if result.error:
            return Score(self.name, 0.0, {"error": result.error})

        raw = result.output.strip()
        match = _JSON_RE.search(raw)
        if not match:
            return Score(self.name, 0.0, {"parse_error": "no JSON found", "raw": raw[:200]})

        try:
            data = json.loads(match.group(0))
            raw_score = float(data["score"])
            reason = str(data.get("reason", ""))[:300]
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            return Score(self.name, 0.0, {"parse_error": str(e), "raw": raw[:200]})

        # 0-10 -> 0.0-1.0, and clamp defensively
        value = max(0.0, min(1.0, raw_score / 10.0))
        return Score(
            name=self.name,
            value=value,
            details={"raw_score": raw_score, "reason": reason},
        )
        