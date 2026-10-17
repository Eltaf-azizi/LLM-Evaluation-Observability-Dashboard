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
