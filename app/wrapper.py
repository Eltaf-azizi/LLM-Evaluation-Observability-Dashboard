"""The logging wrapper. Every LLM call in the app goes through `logged_call`.

Responsibilities:
  1. call the LLM
  2. persist a row in `calls` (prompt, output, model, latency, tokens, cost, error)
  3. run every registered scorer and persist one `scores` row per scorer
  4. return (LLMResult, call_id) so callers can use the output
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Sequence

from .db import connect
from .llm import LLMClient, LLMResult, estimate_cost


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def logged_call(
    prompt: str,
    *,
    prompt_name: str | None = None,
    client: LLMClient | None = None,
    scorers: Sequence = (),
    temperature: float = 0.7,
) -> tuple[LLMResult, int]:
    """Call the LLM, log everything, run scorers, return (result, call_id).

    `prompt_name` is how you tag A/B variants later ('summarize_v1', 'summarize_v2').
    `scorers` is any sequence of objects with `.name` and `.score(prompt, output) -> Score`.
    """
    client = client or LLMClient()
    result = client.complete(prompt, temperature=temperature)
    cost = estimate_cost(result.model, result.prompt_tokens, result.completion_tokens)

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO calls
              (created_at, prompt_name, prompt, output, model, latency_ms,
               prompt_tokens, completion_tokens, total_tokens,
               estimated_cost_usd, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (_now(), prompt_name, prompt, result.output, result.model,
             result.latency_ms, result.prompt_tokens, result.completion_tokens,
             result.total_tokens, cost, result.error),
        )
        call_id = cur.lastrowid

        for scorer in scorers:
            s = scorer.score(prompt, result.output)
            conn.execute(
                """INSERT INTO scores (call_id, scorer, score, details, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (call_id, s.name, float(s.value), json.dumps(s.details), _now()),
            )

    return result, call_id