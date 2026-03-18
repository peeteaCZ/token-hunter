"""
Token Hunter — FastAPI web application.

Start with:
    python scripts/run_server.py
    # or:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import configure_logging
from core.pipeline import Pipeline
from api.pipeline_adapter import adapt_verified_data
from ingestion.file_sources import build_default_sources
from models.llm import ModelEntry
from scoring.best_buy import (
    USE_CASE_PROFILES,
    get_best_for_use_case,
    get_cheapest_models,
    get_free_models,
)
from scoring.best_buy_v1 import get_api_free_models, recommend_best_buy

configure_logging()
logger = logging.getLogger(__name__)

# ── In-memory model cache ─────────────────────────────────────────────────────

_models: list[ModelEntry] = []
_model_debug: dict[str, dict[str, object]] = {}
_non_api_options = []
_pipeline_debug: dict[str, object] = {
    "sources": 0,
    "verified_items": 0,
    "conflicts": 0,
    "last_refresh": None,
}
_last_fetched: datetime | None = None
_data_source = "empty"
_REFRESH_INTERVAL = 3600  # seconds


async def _refresh() -> None:
    global _models, _model_debug, _non_api_options, _pipeline_debug, _last_fetched, _data_source
    logger.info("Refreshing model data from pipeline…")

    try:
        result = Pipeline(
            sources=build_default_sources(),
        ).execute()
        adapted_output = adapt_verified_data(result.records)
        adapted = adapted_output.route_models
    except Exception as exc:
        logger.error("Pipeline refresh failed: %s", exc)
        adapted = []
        adapted_output = None
        result = None

    if adapted:
        _models = [item.model for item in adapted]
        _non_api_options = adapted_output.non_api_options if adapted_output else []
        _model_debug = {
            item.model.id: {
                "evidence": item.evidence,
                "trust_tier": item.trust_tier,
                "conflict_flag": item.conflict_flag,
                "winner_source_id": item.winner_source_id,
                "source_ids": item.source_ids,
                "canonical_model_id": item.canonical_model_id,
                "canonical_route_id": item.canonical_route_id,
                "route_label": item.route_label,
                "route_kind": item.route_kind,
                "friction_flag": item.friction_flag,
                "benefit_summary": item.benefit_summary,
                "effective_cost_note": item.effective_cost_note,
                "pricing_indirect": item.pricing_indirect,
                "confidence": item.confidence,
                "effective_value_hint": item.effective_value_hint,
            }
            for item in adapted
        }
        _last_fetched = datetime.utcnow()
        _pipeline_debug = {
            "sources": result.stats["sources_used"] if result else 0,
            "verified_items": result.stats["verified"] if result else 0,
            "conflicts": result.stats["conflicts_detected"] if result else 0,
            "last_refresh": _last_fetched.isoformat(),
        }
        _data_source = "pipeline"
        logger.info(
            "Loaded %d models from pipeline (%d free)",
            len(_models),
            sum(1 for m in _models if m.is_free),
        )
        logger.info("API data source: %s", _data_source)
        return

    _models = []
    _non_api_options = adapted_output.non_api_options if adapted_output else []
    _model_debug = {}
    _last_fetched = datetime.utcnow()
    _pipeline_debug = {
        "sources": result.stats["sources_used"] if result else 0,
        "verified_items": result.stats["verified"] if result else 0,
        "conflicts": result.stats["conflicts_detected"] if result else 0,
        "last_refresh": _last_fetched.isoformat(),
    }
    _data_source = "pipeline"
    logger.warning("Pipeline returned no verified data")
    logger.info("API data source: %s", _data_source)


async def _background_refresh() -> None:
    while True:
        await asyncio.sleep(_REFRESH_INTERVAL)
        try:
            await _refresh()
        except Exception as exc:
            logger.error("Background refresh failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.wait_for(_refresh(), timeout=30.0)
    except asyncio.TimeoutError:
        logger.warning("Initial fetch timed out — starting with no data")
    except Exception as exc:
        logger.error("Initial fetch failed: %s", exc)
    task = asyncio.create_task(_background_refresh())
    yield
    task.cancel()


# ── App & templates ───────────────────────────────────────────────────────────

app = FastAPI(title="Token Hunter", version="0.1.0", lifespan=lifespan)

_BASE = Path(__file__).parent
_tpl = Jinja2Templates(directory=str(_BASE / "templates"))


def _fmt_price(value: float) -> str:
    if value == 0:
        return "FREE"
    if value < 0.001:
        return f"${value:.5f}"
    if value < 0.01:
        return f"${value:.4f}"
    if value < 1:
        return f"${value:.3f}"
    return f"${value:.2f}"


def _ctx_label(ctx: int) -> str:
    if not ctx:
        return "—"
    return f"{ctx // 1_000_000}M" if ctx >= 1_000_000 else f"{ctx // 1_000}K"


_tpl.env.filters["fmt_price"] = _fmt_price
_tpl.env.filters["ctx_label"] = _ctx_label

# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    no_data_message = "no verified data available" if not _models else None
    return _tpl.TemplateResponse("index.html", {
        "request": request,
        "api_free_models": get_api_free_models(_models, _model_debug, top_n=6),
        "free_models": get_free_models(_models, top_n=9),
        "cheapest_models": get_cheapest_models(_models, top_n=8),
        "coding_models": get_best_for_use_case(_models, "coding_cheap", top_n=5),
        "chat_models": get_best_for_use_case(_models, "chat_cheap", top_n=5),
        "last_fetched": _last_fetched,
        "total_models": len(_models),
        "free_count": sum(1 for m in _models if m.is_free),
        "use_case_profiles": USE_CASE_PROFILES,
        "is_loading": len(_models) == 0,
        "data_source": _data_source,
        "no_data_message": no_data_message,
    })


@app.get("/compare", response_class=HTMLResponse)
async def compare(request: Request, use_case: str = "coding_cheap"):
    if use_case not in USE_CASE_PROFILES:
        use_case = "coding_cheap"
    no_data_message = "no verified data available" if not _models else None
    results = get_best_for_use_case(_models, use_case, top_n=6)
    best = None
    alternatives = []
    explanation = None
    weights_used = None

    if use_case == "api_free":
        results = get_api_free_models(_models, _model_debug, top_n=6)
        best = results[0] if results else None
        alternatives = results[1:] if len(results) > 1 else []
        explanation = "These models are available via API with free quotas or credits, but may have limits."
        weights_used = {"mode": "api_free"}
    elif use_case in {"coding_cheap", "chat_cheap", "reasoning"}:
        recommendation = recommend_best_buy(
            _models,
            _model_debug,
            use_case=use_case,
            top_alternatives=3,
        )
        best = recommendation.winner
        alternatives = recommendation.alternatives
        explanation = recommendation.explanation
        weights_used = recommendation.weights_used
        results = ([best] if best else []) + alternatives

    return _tpl.TemplateResponse("compare.html", {
        "request": request,
        "results": results,
        "best": best,
        "alternatives": alternatives,
        "explanation": explanation,
        "non_api_options": _non_api_options,
        "weights_used": weights_used,
        "use_case": use_case,
        "profile": USE_CASE_PROFILES[use_case],
        "use_case_profiles": USE_CASE_PROFILES,
        "last_fetched": _last_fetched,
        "total_models": len(_models),
        "data_source": _data_source,
        "no_data_message": no_data_message,
    })


@app.get("/ask", response_class=HTMLResponse)
async def ask_get(request: Request):
    return _tpl.TemplateResponse("ask.html", {
        "request": request,
        "answer": None,
        "question": "",
        "last_fetched": _last_fetched,
        "total_models": len(_models),
        "use_case_profiles": USE_CASE_PROFILES,
        "data_source": _data_source,
        "no_data_message": "no verified data available" if not _models else None,
    })


@app.post("/ask", response_class=HTMLResponse)
async def ask_post(request: Request, question: str = Form(...)):
    from api.advisor import ask_advisor
    answer = await ask_advisor(question.strip(), _models)
    return _tpl.TemplateResponse("ask.html", {
        "request": request,
        "answer": answer,
        "question": question,
        "last_fetched": _last_fetched,
        "total_models": len(_models),
        "use_case_profiles": USE_CASE_PROFILES,
        "data_source": _data_source,
        "no_data_message": "no verified data available" if not _models else None,
    })


@app.get("/deal/{model_id:path}", response_class=HTMLResponse)
async def deal_detail(request: Request, model_id: str):
    model = next((m for m in _models if m.id == model_id), None)
    if model is None:
        return _tpl.TemplateResponse(
            "404.html", {"request": request, "model_id": model_id}, status_code=404
        )
    similar = [
        m for m in _models
        if m.id != model_id and (
            m.provider_id == model.provider_id
            or any(t in m.tags for t in model.tags if t != "chat")
        )
    ][:6]
    return _tpl.TemplateResponse("detail.html", {
        "request": request,
        "model": model,
        "similar": similar,
        "last_fetched": _last_fetched,
        "use_case_profiles": USE_CASE_PROFILES,
        "data_source": _data_source,
        "model_debug": _model_debug.get(model.id, {}),
    })


# ── JSON API (iOS-ready) ──────────────────────────────────────────────────────


@app.get("/api/v1/radar")
async def api_radar():
    return {
        "generated_at": _last_fetched.isoformat() if _last_fetched else None,
        "data_source": _data_source,
        "message": None if _models else "no verified data available",
        "total_models": len(_models),
        "free_count": sum(1 for m in _models if m.is_free),
        "best_coding": [
            {"id": c.model.id, "name": c.model.name, "why": c.why, "savings": c.savings_label}
            for c in get_best_for_use_case(_models, "coding_cheap", top_n=3)
        ],
        "best_chat": [
            {"id": c.model.id, "name": c.model.name, "why": c.why, "savings": c.savings_label}
            for c in get_best_for_use_case(_models, "chat_cheap", top_n=3)
        ],
        "top_free": [
            {"id": c.model.id, "name": c.model.name, "provider": c.model.provider_name}
            for c in get_free_models(_models, top_n=5)
        ],
    }


@app.get("/api/v1/models")
async def api_models():
    return {
        "generated_at": _last_fetched.isoformat() if _last_fetched else None,
        "data_source": _data_source,
        "message": None if _models else "no verified data available",
        "count": len(_models),
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider_name,
                "is_free": m.is_free,
                "input_per_1m_usd": m.pricing.input_per_1m,
                "output_per_1m_usd": m.pricing.output_per_1m,
                "context_length": m.context_length,
                "tags": m.tags,
                "evidence": _model_debug.get(m.id, {}).get("evidence"),
                "trust_tier": _model_debug.get(m.id, {}).get("trust_tier"),
                "conflict_flag": _model_debug.get(m.id, {}).get("conflict_flag", False),
                "winner_source_id": _model_debug.get(m.id, {}).get("winner_source_id"),
                "source_ids": _model_debug.get(m.id, {}).get("source_ids", []),
            }
            for m in _models
        ],
    }


@app.get("/api/v1/models/{model_id:path}")
async def api_model_detail(model_id: str):
    from fastapi import HTTPException
    model = next((m for m in _models if m.id == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": model.id,
        "name": model.name,
        "provider_id": model.provider_id,
        "provider_name": model.provider_name,
        "is_free": model.is_free,
        "input_per_1m_usd": model.pricing.input_per_1m,
        "output_per_1m_usd": model.pricing.output_per_1m,
        "context_length": model.context_length,
        "description": model.description,
        "tags": model.tags,
        "openrouter_url": model.openrouter_url,
        "fetched_at": model.fetched_at.isoformat(),
        "data_source": _data_source,
        "evidence": _model_debug.get(model.id, {}).get("evidence"),
        "trust_tier": _model_debug.get(model.id, {}).get("trust_tier"),
        "conflict_flag": _model_debug.get(model.id, {}).get("conflict_flag", False),
        "winner_source_id": _model_debug.get(model.id, {}).get("winner_source_id"),
        "source_ids": _model_debug.get(model.id, {}).get("source_ids", []),
    }


@app.get("/debug/pipeline")
async def debug_pipeline():
    return {
        "number_of_sources": _pipeline_debug["sources"],
        "number_of_verified_items": _pipeline_debug["verified_items"],
        "conflicts": _pipeline_debug["conflicts"],
        "last_refresh": _pipeline_debug["last_refresh"],
        "data_source": _data_source,
        "message": None if _models else "no verified data available",
    }
