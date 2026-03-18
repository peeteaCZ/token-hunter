# PROJECT STATE — Token Hunter
_Snapshot: 2026-03-18_

---

## 1. What Is Implemented

### Domain Models
| File | Models | Status |
|------|--------|--------|
| `models/llm.py` | `PricingInfo`, `ModelEntry`, `DealCard`, `RadarSnapshot` | ✅ Complete |
| `models/token.py` | `RawToken`, `NormalizedToken`, `VerifiedToken`, `RiskLevel` | ✅ (generic skeleton, unused by LLM flow) |

### Ingestion
| Module | Source | Auth | Data |
|--------|--------|------|------|
| `ingestion/openrouter.py` | OpenRouter `/api/v1/models` | None (public) | ~348 models, real pricing |
| `ingestion/base.py` | Abstract base `BaseIngestionSource` | — | Stub only |

Tags are inferred heuristically from model ID, name, and description strings.
Skips `:nitro`, `:extended`, `:beta` variants.

### Scoring
| File | Profiles | Signals |
|------|----------|---------|
| `scoring/best_buy.py` | 6 use-case profiles | price_advantage, tag_fit, context_length, provider_reliability, friction_penalty |

Use-case profiles: `coding_cheap`, `coding_best_value`, `chat_cheap`, `experimentation`, `long_context`, `reasoning`.
Baseline for comparison: GPT-4o mini ($0.15 in / $0.60 out per 1M tokens).
Provider reliability tiers: 3 tiers (0 = unknown, 3 = OpenAI / Anthropic / Google).

### Web Application
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home radar (free, cheapest, best coding, best chat) |
| `/compare` | GET | Use-case selector + ranked results |
| `/ask` | GET/POST | Groq-powered AI advisor (llama-3.3-70b-versatile) |
| `/deal/{model_id}` | GET | Model detail + similar models |
| `/api/v1/radar` | GET | JSON summary for iOS |
| `/api/v1/models` | GET | Full model list JSON |
| `/api/v1/models/{id}` | GET | Single model JSON |

### AI Advisor
- `api/advisor.py`: takes user question + current model list → calls Groq
- System prompt: savings-first, Czech, grounded in radar data only
- Model: `llama-3.3-70b-versatile` via `groq` Python SDK
- Context window: top 8 free + top 10 cheapest + top 5 code models passed as text

### Infrastructure
- **Config**: `config/settings.py` loads from `.env`, `.env.local`, `token_hunter.egg-info/.env.local` (dotenv)
- **Logging**: structured stdout, configurable via `LOG_LEVEL`
- **In-memory cache**: `_models: list[ModelEntry]` in `api/main.py`, refreshed every 3600 s
- **Server**: FastAPI + uvicorn, hot-reload in dev
- **Templates**: Jinja2 with Tailwind CDN, dark theme, Czech UI
- **Tests**: 3 smoke tests covering generic pipeline skeleton

---

## 2. What Is NOT Implemented

### Core Phase 0 Gaps (see zamer/ROADMAP.md)
| Feature | Status | Notes |
|---------|--------|-------|
| Source registry | ❌ | No DB, no source metadata, no trust tiers |
| Multiple ingestion sources | ❌ | Only OpenRouter; no direct provider APIs, no changelog feeds |
| Evidence snapshots | ❌ | No evidence captured or stored — violates DECISIONS.md D6 |
| Parser framework | ❌ | No HTML/doc parser; OpenRouter is API-only |
| Canonical matcher | ❌ | No cross-source deduplication |
| Persistent storage | ❌ | In-memory only; lost on restart |
| Price change detection | ❌ | No historical data |
| Admin source dashboard | ❌ | Not started |

### Phase 1 Gaps (MVP)
| Feature | Status |
|---------|--------|
| Watchlist | ❌ |
| Alerts engine | ❌ |
| Deal detail with evidence trail | ❌ (UI exists but no evidence behind it) |
| Real normalization pipeline | ❌ (tag inference is heuristic) |
| Verification layer | ❌ (always returns `RiskLevel.UNKNOWN`) |

### Other Missing Items
- No route / access-route / offer / plan entities (PRODUCT_MAP.md models)
- No free-tier expiry or time-sensitivity tracking
- No conflict detection between sources
- No stale data flagging
- No search
- No user model / auth
- No scheduled jobs outside in-memory timer

---

## 3. Current Architecture

```
┌──────────────────────────────────────────────┐
│                  api/main.py                  │
│  FastAPI app, in-memory _models cache         │
│  GET / · /compare · /ask · /deal/{id}         │
│  GET /api/v1/*  (iOS-ready JSON)              │
└──────┬──────────────────────┬─────────────────┘
       │ fetch on startup      │ score on request
       ▼                       ▼
┌─────────────────┐   ┌────────────────────────┐
│ ingestion/      │   │ scoring/best_buy.py     │
│ openrouter.py   │   │ 6 use-case profiles     │
│ OpenRouter API  │   │ rule-based scoring      │
└─────────────────┘   └────────────────────────┘
       │
       ▼
┌─────────────────┐
│ models/llm.py   │
│ ModelEntry list │
└─────────────────┘
                          ┌───────────────────┐
           /ask ─────────►│ api/advisor.py    │
                          │ Groq SDK          │
                          │ llama-3.3-70b     │
                          └───────────────────┘
```

**Disconnected skeleton** (not used by web flow):
```
core/pipeline.py → ingestion/base.py → models/token.py → normalization → verification → storage
```
These modules exist but are not called by `api/main.py`.

---

## 4. How the Pipeline Currently Works

1. **Startup** (`api/main.py`, `lifespan`):
   - `_refresh()` → `fetch_openrouter_models()` → HTTP GET to `https://openrouter.ai/api/v1/models`
   - Response parsed: model ID, name, description, pricing, context_length
   - Tags inferred heuristically from text signals
   - Result stored in `_models: list[ModelEntry]` (in-memory)

2. **Request** (e.g. `GET /`):
   - `get_free_models(_models)` — sorts by provider tier, context length
   - `get_cheapest_models(_models)` — sorts by `combined_price`
   - `get_best_for_use_case(_models, "coding_cheap")` — `score_model()` for each
   - Template rendered with results

3. **Scoring** (`scoring/best_buy.py`, `score_model()`):
   - Free bonus (+40 if use-case prefers free)
   - Price advantage (0–30 pts, decay relative to GPT-4o mini baseline)
   - Tag fit (0–20 pts, preferred_tags match)
   - Context score (0–10 pts, up to 128K)
   - Provider reliability (0–15 pts, tier × 5)
   - Friction penalty (−3 for `:free` variant, −5 for unknown provider)

4. **Ask AI** (`POST /ask`):
   - `_build_context(_models)` — top 8 free + top 10 cheapest + top 5 code, formatted as text
   - Groq `chat.completions.create()` with system prompt + context + user question
   - Response rendered in template

5. **Background refresh** (`_background_refresh()`):
   - Runs every 3600 s
   - Re-fetches OpenRouter, replaces `_models`

---

## 5. Known Gaps vs MVP_PLAN

| MVP Must-have | Status | Gap |
|---------------|--------|-----|
| Ingest first key sources | Partial | Only OpenRouter; no official pricing pages, no changelogs |
| Normalize provider/model/route/offer | Partial | ModelEntry exists but no Route or Offer entities |
| Display home radar | ✅ | Live |
| Return best buy for use-case profiles | ✅ | 6 profiles working |
| Show deal detail with evidence trail | ❌ | UI exists; no evidence stored |
| Watchlist | ❌ | Not started |
| Alerts | ❌ | Not started |

---

## 6. Risks and Weak Spots

| Risk | Severity | Detail |
|------|----------|--------|
| No evidence trail | High | Violates D6 (DECISIONS.md). Every verdict must be backed by evidence. |
| Single source | High | Only OpenRouter. No verification against official provider pricing pages. |
| In-memory storage | High | All data lost on restart. Cannot detect price changes. |
| Tag inference fragile | Medium | Heuristic keyword matching. Misclassifies many models. |
| Generic pipeline disconnected | Medium | `core/pipeline.py` unused by web app. Two parallel architectures. |
| Scoring baseline hardcoded | Medium | GPT-4o mini price used as baseline. Will drift as market changes. |
| `.env.local` in egg-info dir | Low | Non-standard; easy to lose on `pip install -e .` rebuild. |
| Groq model hardcoded | Low | `llama-3.3-70b-versatile` — check availability if Groq changes catalog. |
