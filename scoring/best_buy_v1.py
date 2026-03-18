"""
Explainable best-buy engine for pipeline-backed routes.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.llm import DealCard, ModelEntry


@dataclass
class BestBuyRecommendation:
    use_case: str
    winner: DealCard | None
    alternatives: list[DealCard]
    explanation: str
    weights_used: dict[str, float]


USE_CASE_CONFIGS: dict[str, dict[str, object]] = {
    "coding_cheap": {
        "weights": {"price": 1.0, "trust": 0.7, "availability": 0.5, "conflict": 1.0},
        "required_tags": {"code"},
    },
    "chat_cheap": {
        "weights": {"price": 0.8, "trust": 0.8, "availability": 0.5, "conflict": 1.0},
        "required_tags": {"chat"},
    },
    "reasoning": {
        "weights": {"price": 0.35, "trust": 1.2, "availability": 0.5, "conflict": 1.0},
        "required_tags": {"reasoning"},
    },
}


def recommend_best_buy(
    models: list[ModelEntry],
    model_debug: dict[str, dict[str, object]],
    use_case: str,
    *,
    top_alternatives: int = 3,
) -> BestBuyRecommendation:
    config = USE_CASE_CONFIGS.get(use_case, USE_CASE_CONFIGS["coding_cheap"])
    weights = dict(config["weights"])
    required_tags = set(config.get("required_tags", set()))

    candidates = [
        model for model in models
        if _is_available(model, model_debug) and _matches_use_case(model, required_tags)
    ]
    if not candidates:
        return BestBuyRecommendation(
            use_case=use_case,
            winner=None,
            alternatives=[],
            explanation=f"No verified candidates are available for {use_case}.",
            weights_used=weights,
        )

    ranked = sorted(
        ((_build_card(model, model_debug, use_case), _score(model, model_debug, weights)) for model in candidates),
        key=lambda item: item[1],
        reverse=True,
    )
    cards = []
    for card, score_value in ranked:
        card.score = score_value
        cards.append(card)

    for rank, card in enumerate(cards, start=1):
        card.rank = rank

    winner = cards[0]
    alternatives = cards[1:1 + top_alternatives]
    explanation = _build_explanation(winner, alternatives, model_debug, use_case, weights)
    return BestBuyRecommendation(
        use_case=use_case,
        winner=winner,
        alternatives=alternatives,
        explanation=explanation,
        weights_used=weights,
    )


def recommend_coding_cheap(
    models: list[ModelEntry],
    model_debug: dict[str, dict[str, object]],
    *,
    top_alternatives: int = 3,
) -> BestBuyRecommendation:
    return recommend_best_buy(
        models=models,
        model_debug=model_debug,
        use_case="coding_cheap",
        top_alternatives=top_alternatives,
    )


def get_api_free_models(
    models: list[ModelEntry],
    model_debug: dict[str, dict[str, object]],
    *,
    top_n: int = 6,
) -> list[DealCard]:
    candidates = [
        model for model in models
        if _is_api_free_candidate(model, model_debug)
    ]
    grouped: dict[str, list[ModelEntry]] = {}
    for model in candidates:
        canonical_model_id = str(model_debug.get(model.id, {}).get("canonical_model_id", model.id))
        grouped.setdefault(canonical_model_id, []).append(model)

    selected: list[tuple[ModelEntry, list[ModelEntry]]] = []
    for group in grouped.values():
        ranked_group = sorted(group, key=lambda model: _api_free_sort_key(model, model_debug))
        selected.append((ranked_group[0], ranked_group))

    ranked = sorted(selected, key=lambda item: _api_free_sort_key(item[0], model_debug))
    cards: list[DealCard] = []
    for rank, (model, group) in enumerate(ranked[:top_n], start=1):
        debug = model_debug.get(model.id, {})
        hint = dict(debug.get("effective_value_hint", {}))
        free_paths = [_free_access_label(route, model_debug) for route in group]
        best_path = free_paths[0]
        why = f"Free via {best_path}. These models are available via API with free quotas or credits, but may have limits."
        if hint.get("note"):
            why = f"{why} {hint['note']}"
        if len(free_paths) > 1:
            why = f"{why} Other free access paths: {', '.join(free_paths[1:])}."
        cards.append(
            DealCard(
                model=model,
                score=float(rank),
                use_case="api_free",
                rank=rank,
                headline=f"{model.name} — Free API (limited)",
                why=why,
                caveats=_build_caveats(
                    int(debug.get("trust_tier", 3)),
                    bool(debug.get("conflict_flag")),
                    bool(debug.get("friction_flag", False)),
                ),
                savings_label="Free API",
            )
        )
    return cards


def _score(
    model: ModelEntry,
    model_debug: dict[str, dict[str, object]],
    weights: dict[str, float],
) -> float:
    debug = model_debug.get(model.id, {})
    price_component = _price_component(model)
    trust_bonus = {1: 12.0, 2: 6.0, 3: 0.0}.get(int(debug.get("trust_tier", 3)), 0.0)
    conflict_penalty = 15.0 if debug.get("conflict_flag") else 0.0
    availability_bonus = 5.0 if _is_available(model, model_debug) else -100.0
    return (
        price_component * weights["price"]
        + trust_bonus * weights["trust"]
        + availability_bonus * weights["availability"]
        - conflict_penalty * weights["conflict"]
    )


def _build_card(
    model: ModelEntry,
    model_debug: dict[str, dict[str, object]],
    use_case: str,
) -> DealCard:
    debug = model_debug.get(model.id, {})
    trust_tier = int(debug.get("trust_tier", 3))
    why = _build_why(
        model,
        trust_tier,
        bool(debug.get("conflict_flag")),
        str(debug.get("route_label", model.source)),
        str(debug.get("route_kind", "route")),
        str(debug.get("benefit_summary", "")),
        str(debug.get("effective_cost_note", "")),
        dict(debug.get("effective_value_hint", {})),
    )
    caveats = _build_caveats(
        trust_tier,
        bool(debug.get("conflict_flag")),
        bool(debug.get("friction_flag", False)),
    )
    return DealCard(
        model=model,
        score=0.0,
        use_case=use_case,
        rank=0,
        headline=_build_headline(model),
        why=why,
        caveats=caveats,
        savings_label=_build_savings_label(model),
    )


def _price_component(model: ModelEntry) -> float:
    if model.is_free:
        return 100.0
    combined = model.combined_price
    if combined <= 0:
        return 0.0
    return max(0.0, 60.0 - combined * 8.0)


def _is_available(model: ModelEntry, model_debug: dict[str, dict[str, object]]) -> bool:
    debug = model_debug.get(model.id, {})
    return bool(debug.get("evidence")) and bool(debug.get("winner_source_id"))


def _is_api_free_candidate(model: ModelEntry, model_debug: dict[str, dict[str, object]]) -> bool:
    debug = model_debug.get(model.id, {})
    if not _is_available(model, model_debug):
        return False
    if str(debug.get("route_kind", "")) not in {"official", "gateway", "aggregator", "free_tier", "promo"}:
        return False
    hint = dict(debug.get("effective_value_hint", {}))
    return (
        (model.pricing.input_per_1m == 0.0 and model.pricing.output_per_1m == 0.0)
        or str(hint.get("effective_cost_label", "")) == "effectively_free"
    )


def _api_free_sort_key(model: ModelEntry, model_debug: dict[str, dict[str, object]]) -> tuple[float, float, float, str]:
    debug = model_debug.get(model.id, {})
    route_kind = str(debug.get("route_kind", ""))
    direct_provider_priority = 2 if route_kind == "official" and not bool(debug.get("pricing_indirect")) else 1
    return (
        -direct_provider_priority,
        -int(debug.get("trust_tier", 3)),
        -_hint_confidence_rank(str(debug.get("effective_value_hint", {}).get("confidence", ""))),
        -int(debug.get("effective_value_hint", {}).get("approx_tokens", 0)),
        model.name,
    )


def _free_access_label(model: ModelEntry, model_debug: dict[str, dict[str, object]]) -> str:
    debug = model_debug.get(model.id, {})
    route_label = str(debug.get("route_label", model.source))
    if route_label == "Groq API":
        return "Groq API"
    if "OpenRouter" in route_label:
        suffix = "credits" if str(debug.get("route_kind", "")) == "promo" else "free quota"
        return f"OpenRouter ({suffix})"
    return route_label


def _hint_confidence_rank(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(value, 0)


def _matches_use_case(model: ModelEntry, required_tags: set[str]) -> bool:
    if not required_tags:
        return True
    return any(tag in model.tags for tag in required_tags)


def _build_headline(model: ModelEntry) -> str:
    return (
        f"{model.name} — ${model.pricing.input_per_1m:.3f} in / "
        f"${model.pricing.output_per_1m:.3f} out"
    )


def _build_why(
    model: ModelEntry,
    trust_tier: int,
    conflict_flag: bool,
    route_label: str,
    route_kind: str,
    benefit_summary: str,
    effective_cost_note: str,
    effective_value_hint: dict[str, object],
) -> str:
    parts = []
    if effective_cost_note:
        parts.append(f"effective cost with credits: {effective_cost_note}")
    else:
        parts.append(f"observed route cost based on provider price ${model.combined_price:.2f} combined per 1M")
    parts.append(f"route: {route_label}")
    hint_note = _format_effective_value_hint(effective_value_hint)
    if hint_note:
        parts.append(hint_note)
    if trust_tier == 1:
        parts.append("backed by Tier 1 pricing evidence")
    elif trust_tier == 2:
        parts.append("supported by Tier 2 catalog evidence")
    if benefit_summary:
        parts.append(benefit_summary)
    if not conflict_flag:
        parts.append("no active source conflict")
    return ", ".join(parts)


def _build_caveats(trust_tier: int, conflict_flag: bool, friction_flag: bool) -> list[str]:
    caveats: list[str] = []
    if conflict_flag:
        caveats.append("Conflicting source prices detected")
    if trust_tier > 1:
        caveats.append(f"Lower trust tier ({trust_tier}) than official pricing")
    if friction_flag:
        caveats.append("Route may have setup or quota friction")
    return caveats


def _build_savings_label(model: ModelEntry) -> str:
    return f"${model.combined_price:.2f} combined"


def _build_explanation(
    winner: DealCard,
    alternatives: list[DealCard],
    model_debug: dict[str, dict[str, object]],
    use_case: str,
    weights_used: dict[str, float],
) -> str:
    winner_debug = model_debug.get(winner.model.id, {})
    confidence = winner_debug.get("confidence", "n/a")
    parts = [
        f"{winner.model.name} wins for {use_case} because this route has the strongest weighted score.",
        f"It uses trust tier {winner_debug.get('trust_tier', 'n/a')} evidence and "
        f"{'has' if winner_debug.get('conflict_flag') else 'does not have'} an active conflict flag.",
        f"Selected route: {winner_debug.get('route_label', winner.model.source)}.",
        f"Confidence: {confidence}.",
        f"Weights used: price={weights_used['price']}, trust={weights_used['trust']}, availability={weights_used['availability']}, conflict={weights_used['conflict']}.",
    ]
    effective_value_hint = winner_debug.get("effective_value_hint", {})
    if effective_value_hint:
        parts.append(str(effective_value_hint.get("note", "")))
    if winner_debug.get("pricing_indirect") or winner_debug.get("route_kind") in {"gateway", "aggregator", "free_tier", "promo"}:
        parts.append("Confidence is lower because pricing is indirect or route-based rather than provider-direct.")
    if alternatives:
        alt_names = ", ".join(card.model.name for card in alternatives)
        parts.append(f"Alternatives: {alt_names}.")
    return " ".join(parts)


def _format_effective_value_hint(hint: dict[str, object]) -> str:
    note = str(hint.get("note", "")).strip()
    confidence = str(hint.get("confidence", "")).strip()
    if not note:
        return ""
    if confidence:
        return f"{note} Hint confidence: {confidence}."
    return note
