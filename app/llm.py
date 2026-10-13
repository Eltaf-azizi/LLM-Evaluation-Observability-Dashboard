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


    def complete(self, prompt: str, temperature: float = 0.7) -> LLMResult:
        return self._mock_complete(prompt) if self.mock else self._real_complete(prompt, temperature)


    # ---- real provider -------------------------------------------------
    def _real_complete(self, prompt: str, temperature: float) -> LLMResult:
        t0 = time.perf_counter()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            latency = (time.perf_counter() - t0) * 1000
            usage = resp.usage
            return LLMResult(
                output=resp.choices[0].message.content or "",
                model=resp.model or self.model,
                latency_ms=latency,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
        except Exception as e:
            # Never raise. Log the error and let the caller persist it.
            latency = (time.perf_counter() - t0) * 1000
            return LLMResult(
                output="", model=self.model, latency_ms=latency,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                error=f"{type(e).__name__}: {e}",
            )
    
    
    # ---- mock provider -------------------------------------------------
    def _mock_complete(self, prompt: str) -> LLMResult:
        t0 = time.perf_counter()
        time.sleep(0.03)

        # If the judge scorer is calling, emulate its JSON contract so the
        # whole pipeline is testable without an API key.
        if "[[JUDGE_JSON]]" in prompt:
            output = '{"score": 7, "reason": "[MOCK judge] Reasonable answer."}'
        else:
            output = f"[MOCK] Re: '{prompt[:60]}...' — this is a plausible answer."

        latency = (time.perf_counter() - t0) * 1000
        pt = max(1, len(prompt) // 4)
        ct = max(1, len(output) // 4)
        return LLMResult(
            output=output, model="mock", latency_ms=latency,
            prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
        )