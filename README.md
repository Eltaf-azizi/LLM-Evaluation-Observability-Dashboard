 <h1 align="center">LLM Eval & Observability Dashboard</h1>

**Ever wondered if your LLM prompt is actually getting *better* — or just getting *longer*? Yeah. Same.**

So I built this thing. It logs every LLM call you make, scores the outputs with three different scorers, and shows you charts that tell you the truth your vibes have been hiding from you. It's basically Datadog for LLM prompts, but small, hackable, and it runs on SQLite.

Built this as part of my Year 1 handbook grind — but honestly it stopped feeling like an assignment about halfway through and started feeling like something I actually want to ship.

---

## 🎯 The problem I was trying to solve

Here's the thing nobody tells you about prompt engineering:

**You literally cannot tell if your changes helped without scoring.** You tweak a prompt. You eyeball the output. It looks "fine." Ship it. Two weeks later you realize you've been slowly making it worse and *you had no idea* because you were never measuring.

Speed? Measurable. Cost? Measurable. **Quality?** Everybody just vibes it. That's insane.

So the whole point of this project was to answer one question:

> *If I change my prompt from V1 to V2, is V2 actually better? And by how much?*

The answer is now a chart instead of a feeling.

---

## ✨ What it does

- **📝 Logs every LLM call** — prompt, output, latency, tokens, estimated cost, error (if any)
- **🎰 Three pluggable scorers** — keyword/regex, cosine similarity, and LLM-as-judge
- **💾 Persists to SQLite** — one file, zero ops, handles 100k+ rows easily
- **📊 Live dashboard** — score over time, score distribution, cost, token counts
- **🆚 A/B comparison** — see two prompt variants side by side with a green/red winner column
- **🚀 Deploys to Render** — free tier, auto-seeds on cold start, always shows data

