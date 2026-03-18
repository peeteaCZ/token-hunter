# FILE MAP — Token Hunter
_Snapshot: 2026-03-18_

---

## Directory Tree

```
D:\token_hunter\
├── pyproject.toml                  # Project metadata, dependencies
├── setup.cfg                       # (if present) editable install config
├── token_hunter.egg-info/
│   └── .env.local                  # ← GROQ_API_KEY lives here (legacy path)
│
├── .env                            # (optional) base env vars
├── .env.local                      # (optional) local overrides
│
├── api/
│   ├── __init__.py
│   ├── main.py                     # ★ FastAPI app, routes, in-memory cache
│   ├── advisor.py                  # Groq AI advisor (llama-3.3-70b)
│   └── templates/
│       ├── base.html               # Layout: nav, footer, Tailwind CDN
│       ├── index.html              # Home radar (free/cheapest/coding/chat)
│       ├── compare.html            # Use-case selector + ranked results
│       ├── ask.html                # AI advisor form + example questions
│       ├── detail.html             # Model detail + similar models
│       └── 404.html                # Not-found page
│
├── config/
│   ├── __init__.py                 # Re-exports configure_logging, settings
│   └── settings.py                 # Loads .env files, exposes GROQ_API_KEY
│
├── ingestion/
│   ├── __init__.py
│   ├── base.py                     # Abstract BaseIngestionSource (unused by web)
│   └── openrouter.py               # ★ fetch_openrouter_models() — real data
│
├── models/
│   ├── __init__.py
│   ├── llm.py                      # ★ PricingInfo, ModelEntry, DealCard, RadarSnapshot
│   └── token.py                    # Generic token pipeline models (unused by web)
│
├── scoring/
│   ├── __init__.py
│   └── best_buy.py                 # ★ score_model(), 6 USE_CASE_PROFILES
│
├── core/
│   ├── __init__.py
│   └── pipeline.py                 # Generic pipeline skeleton (disconnected)
│
├── normalization/
│   └── __init__.py                 # Stub only
│
├── verification/
│   └── __init__.py                 # Stub only
│
├── storage/
│   └── __init__.py                 # Stub only
│
├── scripts/
│   └── run_server.py               # ★ Entry point: python scripts/run_server.py
│
├── tests/
│   └── test_smoke.py               # 3 smoke tests (generic pipeline skeleton)
│
└── docs/
    └── state/
        ├── PROJECT_STATE.md        # What is / isn't implemented
        ├── FILE_MAP.md             # This file
        ├── RUN_INSTRUCTIONS.md     # How to start
        ├── NEXT_STEPS.md           # What to build next
        └── OPEN_QUESTIONS.md       # Unresolved decisions
```

---

## Key Files — Entry Points

| File | Role |
|------|------|
| `scripts/run_server.py` | **Start here.** Launches uvicorn with hot-reload |
| `api/main.py` | FastAPI app, all routes, in-memory `_models` cache |
| `ingestion/openrouter.py` | Sole live data source — OpenRouter public API |
| `scoring/best_buy.py` | All scoring and ranking logic |
| `api/advisor.py` | Groq integration for `/ask` |
| `config/settings.py` | Env loading; `GROQ_API_KEY` required for `/ask` |

---

## Key Files — Models

| File | Classes |
|------|---------|
| `models/llm.py` | `PricingInfo`, `ModelEntry`, `DealCard`, `RadarSnapshot` |
| `models/token.py` | `RawToken`, `NormalizedToken`, `VerifiedToken`, `RiskLevel` (unused) |

---

## Key Files — Templates

| Template | Route | Notes |
|----------|-------|-------|
| `base.html` | all | Nav + footer; Jinja2 filters `fmt_price`, `ctx_label` available |
| `index.html` | `GET /` | 4 sections: free, cheapest, coding, chat |
| `compare.html` | `GET /compare?use_case=...` | Winner card + up to 6 alternatives |
| `ask.html` | `GET/POST /ask` | Groq advisor; shows `answer` if POST |
| `detail.html` | `GET /deal/{model_id}` | Pricing table + specs + similar models |
| `404.html` | 404 fallback | Simple not-found page |

---

## Disconnected Modules (not called by web app)

These exist as skeleton code and are **not wired into** `api/main.py`:

- `core/pipeline.py`
- `ingestion/base.py`
- `models/token.py`
- `normalization/`
- `verification/`
- `storage/`
