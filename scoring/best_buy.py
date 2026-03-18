"""
Best-buy scoring engine.

Follows the weighting principles from zamer/SCORING_POLICY.md:
  Price Advantage  30 pts
  Use-case Fit     20 pts
  Confidence       15 pts  (via provider reliability tier)
  Context Length   10 pts
  Free-tier bonus  +40 pts (separate lane)
  Friction penalty  -5 pts (rate-limited free tiers, obscure providers)
"""

from __future__ import annotations

from models.llm import DealCard, ModelEntry

# ── Provider reliability tiers (0 = unknown, 3 = most trusted) ───────────────

PROVIDER_RELIABILITY: dict[str, int] = {
    "openai": 3,
    "anthropic": 3,
    "google": 3,
    "mistralai": 2,
    "meta-llama": 2,
    "cohere": 2,
    "deepseek": 2,
    "x-ai": 2,
    "microsoft": 2,
    "perplexity": 2,
    "qwen": 1,
    "01-ai": 1,
    "nousresearch": 1,
    "nvidia": 1,
}

# ── Baseline cost used for Price Advantage score ──────────────────────────────
# GPT-4o mini: $0.15 in / $0.60 out per 1M tokens.
# combined (1:2 ratio) = (0.15 + 0.60*2) / 3 = 0.45
_BASELINE_COMBINED = (0.15 + 0.60 * 2) / 3  # ≈ 0.45 USD/1M

# ── Use-case profiles ─────────────────────────────────────────────────────────

USE_CASE_PROFILES: dict[str, dict] = {
    "coding_cheap": {
        "label": "Coding – nejlevněji",
        "description": "Nejnižší cena s rozumnou schopností generovat kód.",
        "preferred_tags": ["code"],
        "price_weight": 1.0,
        "context_weight": 0.5,
        "free_bonus": True,
    },
    "coding_best_value": {
        "label": "Coding – nejlepší value",
        "description": "Nejlepší poměr kvalita/cena pro každodenní coding.",
        "preferred_tags": ["code"],
        "price_weight": 0.6,
        "context_weight": 0.8,
        "free_bonus": False,
    },
    "chat_cheap": {
        "label": "Chat – nejlevněji",
        "description": "Levný model na každodenní chatování a asistenci.",
        "preferred_tags": ["chat"],
        "price_weight": 1.0,
        "context_weight": 0.3,
        "free_bonus": True,
    },
    "api_free": {
        "label": "Free API",
        "description": "API modely s free quotas nebo credits.",
        "preferred_tags": ["available"],
        "price_weight": 0.0,
        "context_weight": 0.0,
        "free_bonus": False,
    },
    "experimentation": {
        "label": "Experimentování – zdarma/skoro zdarma",
        "description": "Maximální dostupnost bez nákladů. Ideální pro prototypy.",
        "preferred_tags": [],
        "price_weight": 1.0,
        "context_weight": 0.2,
        "free_bonus": True,
    },
    "long_context": {
        "label": "Dlouhý kontext",
        "description": "Modely s velkým kontextovým oknem pro dlouhé dokumenty.",
        "preferred_tags": ["long-context"],
        "price_weight": 0.4,
        "context_weight": 1.5,
        "free_bonus": False,
    },
    "reasoning": {
        "label": "Reasoning / analýza",
        "description": "Modely schopné hloubkového uvažování a komplexní analýzy.",
        "preferred_tags": ["reasoning"],
        "price_weight": 0.4,
        "context_weight": 0.5,
        "free_bonus": False,
    },
}


def _price_advantage_score(model: ModelEntry, price_weight: float) -> float:
    """0–30 pts based on how much cheaper than baseline. Higher = cheaper."""
    if model.is_free:
        return 30.0 * price_weight
    combined = model.combined_price
    if combined <= 0:
        return 0.0
    ratio = combined / _BASELINE_COMBINED
    # Exponential decay: 10× more expensive → near zero, 10× cheaper → ~27 pts
    raw = 30.0 * max(0.0, 1.0 - min(ratio, 8.0) / 8.0)
    return raw * price_weight


def _context_score(model: ModelEntry, context_weight: float) -> float:
    """0–10 pts for context length. 128K = full 10 pts."""
    if not model.context_length:
        return 0.0
    normalized = min(1.0, model.context_length / 128_000)
    return normalized * 10.0 * context_weight


def _tag_fit_score(model: ModelEntry, preferred_tags: list[str]) -> float:
    """0–20 pts for use-case tag match."""
    if not preferred_tags:
        return 10.0  # neutral when no preference
    matching = sum(1 for t in preferred_tags if t in model.tags)
    return (matching / len(preferred_tags)) * 20.0


def _reliability_score(model: ModelEntry) -> float:
    """0–15 pts for provider confidence tier."""
    tier = PROVIDER_RELIABILITY.get(model.provider_id, 0)
    return tier * 5.0


def _friction_penalty(model: ModelEntry) -> float:
    """Negative pts for known friction signals."""
    penalty = 0.0
    if ":free" in model.id:
        penalty += 3.0   # free variants often have strict rate limits
    if PROVIDER_RELIABILITY.get(model.provider_id, 0) == 0:
        penalty += 5.0   # unknown provider
    return penalty


def score_model(model: ModelEntry, use_case: str) -> float:
    profile = USE_CASE_PROFILES.get(use_case, USE_CASE_PROFILES["chat_cheap"])

    score = 0.0

    # Free-tier mega-bonus (makes free models float to the top when preferred)
    if model.is_free and profile.get("free_bonus", False):
        score += 40.0

    score += _price_advantage_score(model, profile["price_weight"])
    score += _tag_fit_score(model, profile["preferred_tags"])
    score += _context_score(model, profile["context_weight"])
    score += _reliability_score(model)
    score -= _friction_penalty(model)

    return max(0.0, score)


# ── Headline / why / caveats helpers ─────────────────────────────────────────

def _fmt_price(value: float) -> str:
    if value == 0:
        return "FREE"
    if value < 0.01:
        return f"${value:.4f}"
    if value < 1:
        return f"${value:.3f}"
    return f"${value:.2f}"


def _build_headline(model: ModelEntry) -> str:
    if model.is_free:
        return f"{model.name} — zdarma"
    inp = _fmt_price(model.pricing.input_per_1m)
    out = _fmt_price(model.pricing.output_per_1m)
    return f"{model.name} — {inp} in / {out} out za 1M tokenů"


def _build_why(model: ModelEntry, use_case: str) -> str:
    parts: list[str] = []
    if model.is_free:
        parts.append("nulové náklady")
    elif model.combined_price < _BASELINE_COMBINED:
        pct = int((1.0 - model.combined_price / _BASELINE_COMBINED) * 100)
        parts.append(f"o {pct}\u202f% levnější než GPT-4o mini")
    if "code" in model.tags and "coding" in use_case:
        parts.append("zaměřen na kód")
    if "reasoning" in model.tags:
        parts.append("silný v reasoning")
    if model.context_length >= 128_000:
        ctx_k = model.context_length // 1_000
        parts.append(f"{ctx_k}K kontextové okno")
    tier = PROVIDER_RELIABILITY.get(model.provider_id, 0)
    if tier == 3:
        parts.append("ověřený provider")
    return ", ".join(parts) if parts else "dobrý poměr cena/výkon"


def _build_caveats(model: ModelEntry) -> list[str]:
    caveats: list[str] = []
    if ":free" in model.id:
        caveats.append("Pomalejší odezva na free tieru (rate limiting)")
    if PROVIDER_RELIABILITY.get(model.provider_id, 0) == 0:
        caveats.append("Méně známý provider — ověř spolehlivost")
    if model.context_length and model.context_length < 8_000:
        caveats.append(f"Krátké kontextové okno ({model.context_length // 1_000}K tokenů)")
    return caveats


def _build_savings_label(model: ModelEntry) -> str:
    if model.is_free:
        return "100% úspora"
    if model.combined_price > 0 and model.combined_price < _BASELINE_COMBINED:
        pct = int((1.0 - model.combined_price / _BASELINE_COMBINED) * 100)
        return f"−{pct}%"
    return ""


# ── Public API ────────────────────────────────────────────────────────────────

def get_best_for_use_case(
    models: list[ModelEntry],
    use_case: str,
    top_n: int = 5,
) -> list[DealCard]:
    scored = sorted(
        ((m, score_model(m, use_case)) for m in models),
        key=lambda x: x[1],
        reverse=True,
    )
    return [
        DealCard(
            model=m,
            score=s,
            use_case=use_case,
            rank=rank,
            headline=_build_headline(m),
            why=_build_why(m, use_case),
            caveats=_build_caveats(m),
            savings_label=_build_savings_label(m),
        )
        for rank, (m, s) in enumerate(scored[:top_n], start=1)
    ]


def get_free_models(models: list[ModelEntry], top_n: int = 12) -> list[DealCard]:
    free = [m for m in models if m.is_free]
    free.sort(key=lambda m: (
        -PROVIDER_RELIABILITY.get(m.provider_id, 0),
        -m.context_length,
        m.name,
    ))
    return [
        DealCard(
            model=m,
            score=100.0,
            use_case="free",
            rank=rank,
            headline=f"{m.name} — zdarma",
            why="Bez poplatků přes OpenRouter",
            caveats=_build_caveats(m),
            savings_label="FREE",
        )
        for rank, m in enumerate(free[:top_n], start=1)
    ]


def get_cheapest_models(models: list[ModelEntry], top_n: int = 10) -> list[DealCard]:
    paid = [m for m in models if not m.is_free and m.combined_price > 0]
    paid.sort(key=lambda m: m.combined_price)
    return [
        DealCard(
            model=m,
            score=max(0.0, 100.0 - rank * 8),
            use_case="cheapest",
            rank=rank,
            headline=_build_headline(m),
            why=_build_why(m, "chat_cheap"),
            caveats=_build_caveats(m),
            savings_label=_build_savings_label(m),
        )
        for rank, m in enumerate(paid[:top_n], start=1)
    ]
