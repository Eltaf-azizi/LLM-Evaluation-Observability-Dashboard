"""FastAPI app. Reads the SQLite DB and exposes JSON endpoints for the dashboard.

Run:
    uvicorn app.main:app --reload
Then open http://localhost:8000/ for the dashboard,
or http://localhost:8000/docs for the interactive API explorer.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db, connect


# --------------------------------------------------------------------------
# Lifespan: runs once on startup. init_db() guarantees the schema exists
# before any request can hit the database.
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()

    # On a fresh container (e.g. Render), the DB is empty. Seed a small
    # demo set so the dashboard is never blank on first load.
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM calls").fetchone()["n"]
    if n == 0:
        # Import lazily so the seed module isn't loaded on every startup.
        import logging
        logging.warning("DB empty — running demo seeder (30 calls)")
        # Import the seeder's logic. We inline a compact version here rather
        # than importing seed.py so we don't ship test scripts to production.
        from .scorers import KeywordScorer, SimilarityScorer, LLMJudgeScorer
        from .wrapper import logged_call
        _scorers = [
            KeywordScorer(required=["hello", "world"]),
            SimilarityScorer(reference="hello world"),
            LLMJudgeScorer(rubric="Should mention hello and world."),
        ]
        for i in range(30):
            variant = "greeting_v1" if i % 2 == 0 else "greeting_v2"
            prompt = (
                "Say hello world." if variant == "greeting_v1"
                else "Say something friendly."
            )
            logged_call(prompt, prompt_name=variant, scorers=_scorers)

    yield
    
# --------------------------------------------------------------------------
# Root — the dashboard.
# --------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# --------------------------------------------------------------------------
# Summary stats for the header cards.
# --------------------------------------------------------------------------
@app.get("/api/summary")
def summary() -> dict:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)                              AS total_calls,
                   COALESCE(SUM(estimated_cost_usd), 0)  AS total_cost_usd,
                   COALESCE(AVG(latency_ms), 0)          AS avg_latency_ms,
                   COALESCE(SUM(total_tokens), 0)        AS total_tokens
            FROM calls
            """
        ).fetchone()
    return dict(row)



# --------------------------------------------------------------------------
# Recent calls list. Query params: limit (int), prompt_name (str, optional).
# --------------------------------------------------------------------------
@app.get("/api/calls")
def list_calls(
    limit: int = Query(20, ge=1, le=500),
    prompt_name: str | None = None,
) -> list[dict]:
    with connect() as conn:
        if prompt_name:
            rows = conn.execute(
                """
                SELECT * FROM calls
                WHERE prompt_name = ?
                ORDER BY id DESC LIMIT ?
                """,
                (prompt_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM calls ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]

