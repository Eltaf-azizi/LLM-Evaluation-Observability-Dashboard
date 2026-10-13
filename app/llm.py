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
