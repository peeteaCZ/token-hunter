# RUN INSTRUCTIONS — Token Hunter
_Snapshot: 2026-03-18_

---

## Prerequisites

- Python **3.10+** (tested on 3.10.6)
- Internet access (fetches OpenRouter API on startup)
- Groq API key (required only for `/ask` — all other routes work without it)

---

## 1. Install dependencies

```bash
cd D:\token_hunter
pip install -e .
```

This installs all packages from `pyproject.toml` and makes the project importable as `token_hunter`.

---

## 2. Set the Groq API key

The key is loaded from the **first** of these files that contains `GROQ_API_KEY`:

1. `D:\token_hunter\token_hunter.egg-info\.env.local`  ← current location
2. `D:\token_hunter\.env.local`
3. `D:\token_hunter\.env`

File format (any of the above):
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Without this key the `/ask` endpoint will fail with a 500 error. The radar, compare, and detail pages work without it.

---

## 3. Start the server

```bash
cd D:\token_hunter
python scripts/run_server.py
```

Output:
```
Token Hunter starting...
  Open: http://localhost:8000
  API:  http://localhost:8000/api/v1/radar
  Stop: Ctrl+C
```

On startup the app fetches ~348 models from OpenRouter (public, no key needed). This takes ~2–5 seconds. The server becomes ready at **http://localhost:8000**.

**Alternative start (direct uvicorn):**
```bash
cd D:\token_hunter
uvicorn api.main:app --reload --port 8000
```

---

## 4. Available URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Home radar (free / cheapest / coding / chat) |
| http://localhost:8000/compare | Use-case selector |
| http://localhost:8000/compare?use_case=reasoning | Specific use-case |
| http://localhost:8000/ask | Groq AI advisor |
| http://localhost:8000/deal/{model_id} | Model detail (e.g. `openai/gpt-4o-mini`) |
| http://localhost:8000/api/v1/radar | JSON summary (iOS-ready) |
| http://localhost:8000/api/v1/models | Full model list JSON |
| http://localhost:8000/api/v1/models/{id} | Single model JSON |

---

## 5. Available use-case profiles

Pass as `?use_case=` query parameter on `/compare`:

| Key | Description |
|-----|-------------|
| `coding_cheap` | Cheapest capable coding model |
| `coding_best_value` | Best quality/price for coding |
| `chat_cheap` | Cheap everyday chat |
| `experimentation` | Free/near-free for experiments |
| `long_context` | Max context window |
| `reasoning` | Best reasoning capability |

---

## 6. Run tests

```bash
cd D:\token_hunter
python -m pytest tests/ -v
```

3 smoke tests covering the generic pipeline skeleton (not the web flow).

---

## 7. Environment variables (optional)

| Variable | Default | Notes |
|----------|---------|-------|
| `GROQ_API_KEY` | — | Required for `/ask` |
| `DEFAULT_COUNTRY` | `CZ` | Not yet used in logic |
| `DEFAULT_LANGUAGE` | `cs` | Not yet used in logic |
| `LOG_LEVEL` | `INFO` | Set to `DEBUG` for verbose output |

---

## 8. Data refresh

Models are fetched once at startup and re-fetched every **3600 seconds** automatically. No manual refresh is needed. Restart the server to force an immediate re-fetch.
