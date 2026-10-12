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

