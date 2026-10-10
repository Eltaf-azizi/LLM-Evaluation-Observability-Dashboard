"""Quick demo seeder — logs a handful of calls under two prompt variants
so /api/ab has something to compare. Phase 5 will replace this with a
proper 100+ call seeder.

Run: python seed_demo.py
"""
from app.db import init_db
from app.scorers import KeywordScorer, SimilarityScorer, LLMJudgeScorer
from app.wrapper import logged_call

init_db()

scorers = [
    KeywordScorer(required=["hello", "world"]),
    SimilarityScorer(reference="hello world"),
    LLMJudgeScorer(rubric="Greeting should mention 'hello' and 'world'."),
]

# Variant A: straight, explicit — should score high on keyword.
variant_a = [
    "Say hello world.",
    "Say hello world again.",
    "Please say hello world.",
    "Reply with: hello world.",
    "Echo back hello world.",
]

# Variant B: vague, indirect — should score low on keyword.
variant_b = [
    "Greet the planet.",
    "Compose a salutation.",
    "Say hi to everyone.",
    "Welcome the user.",
    "Address the globe.",
]

for prompt in variant_a:
    logged_call(prompt, prompt_name="greeting_v1", scorers=scorers)

for prompt in variant_b:
    logged_call(prompt, prompt_name="greeting_v2", scorers=scorers)

print("Seeded 5 calls per variant (greeting_v1, greeting_v2).")