 <h1 align="center">LLM Eval & Observability Dashboard</h1>

**Ever wondered if your LLM prompt is actually getting *better* — or just getting *longer*? Yeah. Same.**

So I built this thing. It logs every LLM call you make, scores the outputs with three different scorers, and shows you charts that tell you the truth your vibes have been hiding from you. It's basically Datadog for LLM prompts, but small, hackable, and it runs on SQLite.

Built this as part of my Year 1 handbook grind — but honestly it stopped feeling like an assignment about halfway through and started feeling like something I actually want to ship.

---

## The problem I was trying to solve

Here's the thing nobody tells you about prompt engineering:

**You literally cannot tell if your changes helped without scoring.** You tweak a prompt. You eyeball the output. It looks "fine." Ship it. Two weeks later you realize you've been slowly making it worse and *you had no idea* because you were never measuring.

Speed? Measurable. Cost? Measurable. **Quality?** Everybody just vibes it. That's insane.

So the whole point of this project was to answer one question:

> *If I change my prompt from V1 to V2, is V2 actually better? And by how much?*

The answer is now a chart instead of a feeling.

---

## What it does

- ** Logs every LLM call** — prompt, output, latency, tokens, estimated cost, error (if any)
- ** Three pluggable scorers** — keyword/regex, cosine similarity, and LLM-as-judge
- ** Persists to SQLite** — one file, zero ops, handles 100k+ rows easily
- ** Live dashboard** — score over time, score distribution, cost, token counts
- ** A/B comparison** — see two prompt variants side by side with a green/red winner column
- ** Deploys to Render** — free tier, auto-seeds on cold start, always shows data

---

## 📸 Screenshots

> *[ Add 2-3 screenshots here — the dashboard, the /docs page, and the A/B table. Take them with Win+Shift+S, drag into the README editor in GitHub, and GitHub will host them for you. ]*

---

## Architecture

The whole thing is deliberately boring on the infra side — no Kubernetes, no Redis, no microservices. Just FastAPI + SQLite + vanilla JS. Because I'm 17 and I don't have time to debug Kubernetes, and *neither should you*.
```
┌──────────────────────────────────────────────┐
│ Browser (Chart.js dashboard) │
└───────────────────┬──────────────────────────┘
│ fetch() JSON
┌───────────────────▼──────────────────────────┐
│ FastAPI │
│ /api/summary /api/calls │
│ /api/scores/timeseries │
│ /api/scores/distribution │
│ /api/ab │
└───────────────────┬──────────────────────────┘
│ Python
┌───────────────────▼──────────────────────────┐
│ logged_call() wrapper │
│ 1. call LLM 2. time it 3. INSERT call │
│ 4. run scorers 5. INSERT scores │
└───┬──────────────────────────────────┬───────┘
│ │
┌───▼────────────┐ ┌──────────▼───────┐
│ LLMClient │ │ Scorers │
│ OpenAI- │ │ • keyword │
│ compatible │ │ • similarity │
│ (works w/ │ │ • llm_judge │
│ Groq, Ollama, │ │ │
│ OpenAI, LM │ │ │
│ Studio) │ │ │
└────────────────┘ └──────────────────┘
```

---

### Two decisions that made everything else easy

**1. `calls` and `scores` are separate tables.**
One call → many scores (one per scorer). This is what makes scorers *pluggable*. Want a fourth scorer? Register it. Next call logs four scores instead of three. Zero schema changes, zero wrapper changes.

**2. Every scorer returns `0.0 – 1.0`.**
Clamped defensively in a `Score` dataclass. This is what makes the charts *honest*. If keyword returns 0-1 and judge returns 0-10, the chart lies. Force everything into the same range and the chart tells the truth.

---

## 🚀 Running it locally

```bash
git clone https://github.com/YOUR_USERNAME/llm-eval-dashboard.git
cd llm-eval-dashboard

python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
cp .env.example .env       # leave LLM_API_KEY empty for mock mode

# Optional: seed some data so the dashboard isn't empty
python seed.py

# Start the server
uvicorn app.main:app --reload

Then open:

 - http://localhost:8000/ — the dashboard
 - http://localhost:8000/docs — FastAPI's auto-generated API explorer (this thing is chef's kiss)
```

## The three scorers (and why there are three)

`keyword`  the dumbest, most useful one
Score = fraction of required keywords that appear in the output. Optional banned-word list (score goes to 0.0 if any are hit).

Looks naive. Isn't. It's free, deterministic, and instant. It's the scorer that tells you whether your prompt change actually made the model use the words you wanted. Every eval suite in production starts here  even OpenAI's own benchmarks use this class of scorer.

`similarity`  cosine over bag-of-words
Turn both output and reference answer into token-count vectors, then compute cosine similarity. It's the mathematical "how alike are these two texts" that doesn't require a PhD.

Known weakness: it punishes verbosity. If your reference is "hello world" (2 tokens) and your output is 20 tokens, similarity is low even if the output is great. That's the bag-of-words tax. Upgrade path: swap the vectorizer for an embeddings call and you get semantic similarity for free — same scorer interface, better signal.

`llm_judge`  the most powerful and most dangerous
Ask a judge model: "given this rubric, rate this output 0–10 with one reason." Parse the JSON. Normalize to 0–1.

Three things I learned the hard way:

 1. Judges are biased. They prefer longer answers. They prefer outputs from their own model family. They're order-sensitive. Never trust a judge score in isolation.
 2. Always ask for JSON. Prose is unparseable, and an unparseable judge is worse than no judge at all.
 3. Always have a fallback. If JSON parsing fails, log the raw response and score 0.0. Never let one bad judge call crash your pipeline.

## What I actually learned building this
Not gonna lie — this project taught me more than any tutorial could, because I had to feel the pain of each thing:

 - GROUP BY date(created_at) — I thought SQL aggregation was boring. Then I needed to fit 120 calls into a 7-point line chart. Suddenly it's the most useful line of code in the app.
 - Ephemeral filesystems are real — I seeded 120 calls, checked back in an hour, and the dashboard was empty. Turns out Render's free tier spins down containers and wipes the disk. Fixed it with a startup hook that auto-    seeds if the DB is empty. That's a lesson you don't get from a blog post.
 - Mocks leak into metrics — my mock returns prompt[:60] echoed back. Some keywords got truncated. So my "keyword score" wasn't 1.0 even when the prompt clearly said the word. The numbers were real, but they were      measuring the mock, not the prompt. Never trust absolute values from mock data. Only trust relative comparisons.
 - % vs %% — spent 10 minutes debugging a sqlite3.OperationalError: near "%" because I used %% in an f-string. f-strings and old %-formatting are different worlds. What a way to learn.
 - --host 0.0.0.0 — hard-coding localhost works on your laptop and fails in a container. The container has its own localhost. 0.0.0.0 means "listen on every interface" which is what a cloud host's proxy needs. Small flag,  huge lesson.

## Definition of Done (yes I actually checked these)
 - Logs ≥100 calls (120 demo calls across 2 prompt variants)
 - A/B comparison works and is visibly different (demo_v1: 0.742 keyword / demo_v2: 0.000)
 - Charts render (line chart, histogram, A/B table — all live)
 - Deployed to Render (link below)

## Roadmap (things I want to add next)
The current app answers "which prompt is better?" The next things answer "did it get worse?" and "how do I show this to someone who doesn't have the dashboard open?" — both of those are what turn a demo into a real product.

 - Regression alerts email/Slack notification when average score drops > 10% week-over-week
 - PDF export — one-click report of the current week's stats, so I can send it to someone
 - Embedding-based similarity — swap bag-of-words for real semantic similarity
 - Prompt versioning UI — manage prompt variants without editing Python files
 - Persistent disk on Render — $5/month, fixes the "DB vanishes" problem properly
 - Turso migration — managed SQLite in the cloud, no more persistence worries
None of these are "someday maybe" — they're all speced out and one weekend away. This project is alive.

## Tech stack
 - Backend: FastAPI + Uvicorn
 - Database: SQLite (with WAL mode for concurrent read/write)
 - LLM client: openai-python (works with any OpenAI-compatible endpoint)
 - Frontend: Vanilla HTML/CSS/JS + Chart.js via CDN
 - Deploy: Render free tier

No frameworks used that I couldn't explain. No React, no Docker, no Terraform. Every layer is something I can debug at 2 AM without Googling the error message.
