"""SQLite layer. Everything the app persists lives here.

Why SQLite?
  * Single file, zero setup, built into Python.
  * Handles 100k+ rows fine for a dashboard.
  * WAL mode lets a reader (dashboard) and a writer (logger) coexist.

Two tables:
  calls  -- one row per LLM call
  scores -- one row per (call, scorer); this is what makes scorers pluggable
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eval.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at         TEXT    NOT NULL,         -- ISO-8601 UTC
    prompt_name        TEXT,                     -- e.g. 'summarize_v1' / 'summarize_v2'
    prompt             TEXT    NOT NULL,
    output             TEXT,
    model              TEXT,
    latency_ms         REAL,
    prompt_tokens      INTEGER,
    completion_tokens  INTEGER,
    total_tokens       INTEGER,
    estimated_cost_usd REAL,
    error              TEXT                      -- NULL on success
);

CREATE TABLE IF NOT EXISTS scores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id    INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    scorer     TEXT    NOT NULL,                 -- 'keyword', 'similarity', 'llm_judge'
    score      REAL    NOT NULL,                 -- always 0.0 .. 1.0
    details    TEXT,                             -- JSON blob with per-scorer info
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_calls_created     ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_calls_prompt_name ON calls(prompt_name);
CREATE INDEX IF NOT EXISTS idx_scores_call       ON scores(call_id);
CREATE INDEX IF NOT EXISTS idx_scores_scorer     ON scores(scorer);
"""

