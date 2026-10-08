"""Run: python smoke_test.py — Phase 1 verification."""
from app.db import init_db, connect
from app.wrapper import logged_call

init_db()

result, call_id = logged_call(
    "Say hello in exactly one word.",
    prompt_name="smoke_test",
)
print(f"call_id       = {call_id}")
print(f"output        = {result.output!r}")
print(f"model         = {result.model}")
print(f"latency_ms    = {result.latency_ms:.1f}")
print(f"tokens        = {result.total_tokens} "
      f"(prompt={result.prompt_tokens}, completion={result.completion_tokens})")
print(f"error         = {result.error}")

with connect() as conn:
    row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()

print("\nDB row:")
for key in row.keys():
    print(f"  {key:20s} = {row[key]}")