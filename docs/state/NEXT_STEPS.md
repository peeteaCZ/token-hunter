# NEXT STEPS — Token Hunter
_Snapshot: 2026-03-18_

Priority order: Phase 0 gaps must be closed before Phase 1 features.

---

## Phase 0 — Fix Critical Gaps (blockers for trustworthiness)

### 0-A: Add a second ingestion source
**Why:** Currently the only source is OpenRouter. We cannot verify prices or detect discrepancies.
**What:** Add ingestion from at least one official provider pricing page (e.g. Anthropic, OpenAI, or Google pricing pages). Even a manual JSON snapshot checked in as `data/pricing_overrides.json` would be an improvement.
**Files to create/modify:** `ingestion/anthropic.py` or `data/pricing_overrides.json`, `ingestion/base.py` (implement properly), `api/main.py` (merge sources).

### 0-B: Capture evidence snapshots
**Why:** DECISIONS.md D6 states every verdict must be backed by evidence. Currently nothing is stored — a model's price could change and we'd have no record.
**What:** Save raw API response JSON to `data/snapshots/{date}-openrouter.json` on each fetch.
**Files to create/modify:** `ingestion/openrouter.py` (add save step), new `storage/snapshots.py`.

### 0-C: Persistent storage
**Why:** All data is lost on restart. Cannot detect price changes over time.
**What:** Write fetched models to SQLite via `aiosqlite` or simple JSON files. Load on startup if OpenRouter is unreachable.
**Files to create/modify:** New `storage/db.py` or `storage/json_store.py`, modify `api/main.py` lifespan.

### 0-D: Price change detection
**Why:** The core value proposition is alerting users to price changes.
**What:** Compare new fetch to stored previous snapshot. Emit `PriceChangeEvent` records when `input_per_1m` or `output_per_1m` changes by >1%.
**Files to create/modify:** New `scoring/changes.py`, requires 0-C.

---

## Phase 1 — MVP Features

### 1-A: Watchlist
**What:** Allow users to mark models they care about. Store in browser localStorage (client-side) or a simple server-side list.
**Files to create/modify:** New `api/templates/watchlist.html`, JS in `base.html` or a new script.

### 1-B: Alerts / notifications
**What:** Email or webhook notification when a watched model's price drops or a new free tier appears.
**Requires:** 0-C (persistence), 0-D (change detection).

### 1-C: Evidence trail on deal detail page
**Why:** `detail.html` exists but shows no source provenance. Users must trust the numbers blindly.
**What:** Show "fetched from OpenRouter at {time}" + link to raw API response or snapshot file.
**Files to modify:** `detail.html`, `api/main.py` deal_detail route, requires 0-B.

### 1-D: Real tag normalization
**Why:** Tags are currently inferred by keyword matching on model ID/name/description. Many models are misclassified.
**What:** Build a tag map: explicit `model_id → [tags]` overrides + smarter heuristics. Or use a small LLM call to classify.
**Files to modify:** `ingestion/openrouter.py` `_infer_tags()`, or new `normalization/tags.py`.

---

## Phase 2 — Polish & Growth

### 2-A: Search
Add a search box on the home/compare page. Filter `_models` list by name/provider client-side (JS) or server-side.

### 2-B: Fix disconnected pipeline
Wire `core/pipeline.py` → `ingestion/base.py` → `models/token.py` into the actual web flow, or delete the skeleton entirely to reduce confusion.

### 2-C: Move baseline price to config
`_BASELINE_COMBINED = 0.45` is hardcoded in `scoring/best_buy.py`. Move to `config/settings.py` so it can be updated without a code change.

### 2-D: Stale data flagging
If `_last_fetched` is > 2 hours ago, show a warning banner in the UI.

### 2-E: iOS / mobile-native integration
The `/api/v1/radar` endpoint is already iOS-ready. Next: document the schema, add versioning (`/api/v2/`), add `ETag`/`Last-Modified` headers for efficient polling.

---

## Immediate Low-Hanging Fruit (< 1 hour each)

| Task | File | Effort |
|------|------|--------|
| Move scoring baseline to config | `scoring/best_buy.py`, `config/settings.py` | 15 min |
| Add stale-data warning banner | `base.html`, `api/main.py` | 20 min |
| Add `data/` directory with `.gitkeep` | — | 2 min |
| Write `.gitignore` (exclude `.env*`, `*.egg-info`) | root | 5 min |
| Add `GROQ_API_KEY` validation on startup with clear error message | `api/main.py` lifespan | 10 min |
