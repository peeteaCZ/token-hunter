# OPEN QUESTIONS — Token Hunter
_Snapshot: 2026-03-18_

Unresolved decisions that will affect architecture. Each needs an explicit answer before building the related feature.

---

## Architecture

**Q1: What is the canonical persistence layer?**
Options: SQLite (`aiosqlite`), flat JSON files in `data/`, PostgreSQL, or stay in-memory.
_Impact:_ Affects how price change detection, watchlist, and evidence trail are implemented.
_Lean:_ SQLite for local dev simplicity; can upgrade to Postgres later.

**Q2: Should the disconnected pipeline (`core/pipeline.py`, `models/token.py`, etc.) be deleted or wired in?**
Two parallel architectures exist. Either remove the dead code or commit to using it.
_Impact:_ The generic pipeline was designed for multi-source token data, not LLM pricing. It may not fit.
_Lean:_ Delete if not used within Phase 1.

**Q3: Multi-process / multi-instance deployment?**
The in-memory cache (`_models`) is per-process. If deployed with multiple uvicorn workers, each process fetches independently and may have different data.
_Impact:_ For production deployment, cache must move to Redis or a shared DB.

---

## Data & Sources

**Q4: Which official provider pricing pages should be scraped/parsed?**
Candidates: `openai.com/pricing`, `anthropic.com/pricing`, `ai.google.dev/pricing`.
_Impact:_ Determines how much HTML parsing work is needed vs. API availability.

**Q5: How should price conflicts between sources be resolved?**
If OpenRouter shows $0.15/1M but the official page shows $0.20/1M, which wins?
_Impact:_ Needs a conflict resolution policy before implementing the canonical matcher.
_See:_ DECISIONS.md (conflict detection not yet implemented).

**Q6: Should `:free` variant models be treated as separate entries or as a flag on the base model?**
Currently `:free` variants are kept as separate `ModelEntry` objects and penalized with a friction score.
_Impact:_ Affects deduplication logic and how "free tier" is displayed.

---

## Scoring

**Q7: Should the scoring baseline ($0.45 combined) be dynamic (median of all models) or a fixed reference point (GPT-4o mini)?**
Currently hardcoded as GPT-4o mini approximate. The market moves.
_Impact:_ If baseline drifts significantly, all price_advantage scores become misleading.

**Q8: Should tag inference be replaced with an LLM classification call?**
Heuristic keyword matching misclassifies models. A one-time Groq call per model could be much more accurate.
_Impact:_ Would require caching classification results (needs persistence — see Q1).

---

## Product

**Q9: Who is the primary user — a developer optimizing API spend, or a non-technical user looking for the "best AI"?**
The current Czech UI and "savings-first" framing suggests developers. But the AI advisor feature (`/ask`) could serve non-technical users.
_Impact:_ Affects copy, navigation, onboarding, and which features get prioritized.
_See:_ PROJECT_COMPASS.md (target user definition).

**Q10: Should the Groq advisor respond in Czech always, or detect language from the question?**
Currently the system prompt instructs Czech responses only.
_Impact:_ English-speaking users get Czech answers. Simple fix: detect language or add a `lang` parameter.

**Q11: Is this a public SaaS product or an internal/personal tool?**
Currently no auth, no rate limiting, no user accounts. Fine for personal use but not for public deployment.
_Impact:_ Auth, rate limiting, and cost controls (Groq calls cost money) are needed before going public.

---

## Infrastructure

**Q12: What is the deployment target?**
Options: local only, fly.io, Railway, VPS, Vercel (Python not supported).
_Impact:_ Affects whether SQLite is viable (persistent disk) vs. need for managed DB.

**Q13: Should `.env.local` in `token_hunter.egg-info/` stay as the canonical key location?**
This is a non-standard path that gets regenerated on `pip install -e .`. Easy to lose keys.
_Impact:_ Should migrate to `D:\token_hunter\.env.local` as the primary location.
