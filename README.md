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
