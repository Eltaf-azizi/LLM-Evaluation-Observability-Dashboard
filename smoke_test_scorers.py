"""Run: python smoke_test_scorers.py
Logs 3 calls, each scored by all three scorers. Prints the results.
"""
from app.db import init_db, connect
from app.scorers import KeywordScorer, SimilarityScorer, LLMJudgeScorer
from app.wrapper import logged_call

init_db()

scorers = [
    KeywordScorer(required=["hello", "world"], banned=["error"]),
    SimilarityScorer(reference="hello world"),
    LLMJudgeScorer(rubric="Answer should greet the user and mention 'world'."),
]

prompts = [
    "Say hello and mention the world.",
    "Greet the user warmly and talk about planet Earth.",
    "What's the weather?",
]

for p in prompts:
    result, call_id = logged_call(p, prompt_name="scorer_smoke", scorers=scorers)
    print(f"\ncall_id={call_id}  prompt={p!r}")
    print(f"  output: {result.output[:70]}")

with connect() as conn:
    rows = conn.execute(
        """
        SELECT c.id AS call_id, c.prompt, s.scorer, s.score, s.details
        FROM calls c JOIN scores s ON s.call_id = c.id
        WHERE c.prompt_name = 'scorer_smoke'
        ORDER BY c.id, s.scorer
        """
    ).fetchall()

print("\n--- scores ---")
for r in rows:
    print(f"  call {r['call_id']}  {r['scorer']:11s} = {r['score']:.3f}   {r['details'][:90]}")