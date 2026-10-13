"""Thin adapter over an OpenAI-compatible chat completions endpoint.

Works with: OpenAI, Groq, Together, Fireworks, Ollama (/v1), vLLM, LM Studio.
If LLM_API_KEY is empty, falls back to MOCK mode so you can develop offline.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# USD per 1,000,000 tokens: (input_price, output_price)
# Update as providers change prices. Missing model -> cost 0.
PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini":            (0.15,  0.60),
    "gpt-4o":                 (2.50, 10.00),
    "gpt-3.5-turbo":          (0.50,  1.50),
    "llama-3.1-8b-instant":   (0.05,  0.08),   # Groq
    "llama-3.3-70b-versatile":(0.59,  0.79),   # Groq
    "mock":                   (0.00,  0.00),
}

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_p, out_p = PRICING.get(model, (0.0, 0.0))
    return (prompt_tokens * in_p + completion_tokens * out_p) / 1_000_000


@dataclass
class LLMResult:
    output: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    error: Optional[str] = None


class LLMClient:
    """One method: `.complete(prompt) -> LLMResult`. Never raises."""

    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.mock = not self.api_key

        if not self.mock:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    