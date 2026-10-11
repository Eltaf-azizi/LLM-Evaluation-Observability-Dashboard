"""Seed 120 demo calls across two prompt variants for the dashboard.

Usage:
    python seed.py               # seed fresh (wipes previous demo_* data)
    python seed.py --keep        # add to existing data instead of wiping
    python seed.py --n 200       # seed a different number of calls (default 120)

What it does:
    1. Optionally wipes rows where prompt_name starts with 'demo_'
    2. Logs N calls alternating between demo_v1 and demo_v2
    3. Runs all 3 scorers on each
    4. Backdates created_at across the last 7 days so the timeseries chart has shape
"""
from __future__ import annotations

import argparse
import random

from app.db import init_db, connect
from app.scorers import KeywordScorer, SimilarityScorer, LLMJudgeScorer
from app.wrapper import logged_call


# --------------------------------------------------------------------------
# Prompt variants. Two plausible strategies for the same task.
# --------------------------------------------------------------------------
VARIANT_PROMPTS = {
    "demo_v1": [
        "Reply with exactly two sentences and include the words 'hello' and 'world'.",
        "In two sentences, greet the world and say hello. Use the words 'hello' and 'world'.",
        "Write a two-sentence greeting that contains the words 'hello' and 'world'.",
        "Compose exactly two sentences saying hello to the world.",
        "Give a two-sentence reply, mentioning 'hello' and 'world' explicitly.",
    ],
    "demo_v2": [
        "Say something friendly.",
        "Write a nice greeting.",
        "Compose a warm message for the user.",
        "Give a pleasant reply.",
        "Respond in a friendly way.",
    ],
}
