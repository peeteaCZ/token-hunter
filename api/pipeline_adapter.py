"""
Adapter from verified pipeline records to UI-facing ModelEntry objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.pipeline import VerifiedDataRecord
from models.llm import ModelEntry, NonApiOption, PricingInfo

PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "groq": "Groq",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "meta-llama": "Meta",
    "mistralai": "Mistral AI",
    "cohere": "Cohere",
    "qwen": "Qwen / Alibaba",
    "deepseek": "DeepSeek",
    "microsoft": "Microsoft",
    "amazon": "Amazon",
    "01-ai": "01.AI",
    "perplexity": "Perplexity",
    "nousresearch": "Nous Research",
    "x-ai": "xAI",
    "openrouter": "OpenRouter",
}


@dataclass
class AdaptedModelData:
    model: ModelEntry
    evidence: dict[str, object]
    trust_tier: int
    conflict_flag: bool
    winner_source_id: str
    source_ids: list[str]
    canonical_model_id: str
    canonical_route_id: str
    route_label: str
    route_kind: str
    friction_flag: bool
    benefit_summary: str
    effective_cost_note: str
    pricing_indirect: bool
    confidence: float
    effective_value_hint: dict[str, object]


@dataclass
class AdaptedPipelineOutput:
    route_models: list[AdaptedModelData]
    non_api_options: list[NonApiOption]


def adapt_verified_data(records: Iterable[VerifiedDataRecord]) -> AdaptedPipelineOutput:
    official_prices: dict[str, tuple[float, float]] = {}
    for record in records:
        price = record.price_snapshot
        if price is None:
            continue
        if int(record.trust_tier) == 1 and str(price.metadata.get("route_kind", "")) == "official":
            canonical_route_id = str(price.metadata.get("canonical_route_id", price.route_id))
            official_prices[canonical_route_id] = (float(price.input_price), float(price.output_price))

    adapted: list[AdaptedModelData] = []
    non_api_options: list[NonApiOption] = []
    for winner in records:
        price = winner.price_snapshot
        if price is None:
            offer = winner.offer
            if offer is not None and str(offer.metadata.get("access_type", "api")) != "api":
                non_api_options.append(
                    NonApiOption(
                        model_name=str(offer.metadata.get("model_name") or offer.title),
                        access_type=str(offer.metadata.get("access_type", "platform_ui")),
                        access_description=str(offer.metadata.get("access_description") or offer.headline_value),
                        usage_limits=str(offer.metadata.get("usage_limits", "")),
                        notes=str(offer.metadata.get("notes", "")),
                        source=winner.evidence.url,
                        not_included_reason=_not_included_reason(
                            access_type=str(offer.metadata.get("access_type", "platform_ui")),
                        ),
                    )
                )
            continue

        canonical_route_id = str(price.metadata.get("canonical_route_id", price.route_id))
        provider_id = str(price.metadata.get("provider_id", canonical_route_id.split("/")[0]))
        provider_name = PROVIDER_DISPLAY_NAMES.get(provider_id, provider_id.replace("-", " ").title())
        official_input_price, official_output_price = official_prices.get(
            canonical_route_id,
            (float(price.input_price), float(price.output_price)),
        )
        trust_tier = int(winner.trust_tier)
        conflict_flag = winner.conflict_flag
        source_ids = list(winner.verified.source_ids or [winner.verified.source_id])
        route_label = str(price.metadata.get("route_label", winner.verified.source_id))
        route_kind = str(price.metadata.get("route_kind", "route"))
        friction_flag = bool(price.metadata.get("friction_flag", False))
        availability = bool(price.metadata.get("availability", True))
        benefit_summary = str(price.metadata.get("benefit_summary", ""))
        effective_cost_note = str(price.metadata.get("effective_cost_note", ""))
        pricing_indirect = bool(price.metadata.get("pricing_indirect", trust_tier > 1))
        confidence = _confidence_for_route(
            trust_tier=trust_tier,
            route_kind=route_kind,
            pricing_indirect=pricing_indirect,
            conflict_flag=conflict_flag,
        )
        effective_value_hint = _effective_value_hint(
            route_kind=route_kind,
            benefit_summary=benefit_summary,
            effective_cost_note=effective_cost_note,
        )

        tags = list(price.metadata.get("tags", []))
        for tag in _infer_capability_tags(canonical_route_id):
            if tag not in tags:
                tags.append(tag)
        if "evidence-available" not in tags:
            tags.append("evidence-available")
        if f"trust-tier-{trust_tier}" not in tags:
            tags.append(f"trust-tier-{trust_tier}")
        if conflict_flag and "conflict" not in tags:
            tags.append("conflict")
        if winner.verified.source_count > 1 and "multi-source" not in tags:
            tags.append("multi-source")
        if route_kind not in tags:
            tags.append(route_kind)
        if friction_flag and "friction" not in tags:
            tags.append("friction")
        if pricing_indirect and "pricing-indirect" not in tags:
            tags.append("pricing-indirect")
        if availability and "available" not in tags:
            tags.append("available")

        evidence = winner.evidence
        model = ModelEntry(
            id=price.route_id,
            name=f"{_display_name(canonical_route_id)} via {route_label}",
            provider_id=provider_id,
            provider_name=provider_name,
            pricing=PricingInfo(
                input_per_1m=official_input_price,
                output_per_1m=official_output_price,
                is_free=(official_input_price == 0.0 and official_output_price == 0.0),
            ),
            context_length=int(price.metadata.get("context_length", 0)),
            description=_build_description(winner, source_ids),
            tags=tags,
            source=f"pipeline:{winner.verified.winner_source_id}",
            fetched_at=evidence.captured_at,
        )
        adapted.append(
            AdaptedModelData(
                model=model,
                evidence={
                    "title": evidence.title,
                    "url": evidence.url,
                    "excerpt": evidence.excerpt,
                    "captured_at": evidence.captured_at.isoformat(),
                    "source_id": evidence.source_id,
                },
                trust_tier=trust_tier,
                conflict_flag=conflict_flag,
                winner_source_id=winner.verified.winner_source_id,
                source_ids=source_ids,
                canonical_model_id=str(price.metadata.get("canonical_model_id", canonical_route_id.split("/", 1)[1])),
                canonical_route_id=canonical_route_id,
                route_label=route_label,
                route_kind=route_kind,
                friction_flag=friction_flag,
                benefit_summary=benefit_summary,
                effective_cost_note=effective_cost_note,
                pricing_indirect=pricing_indirect,
                confidence=confidence,
                effective_value_hint=effective_value_hint,
            )
        )

    adapted.sort(key=lambda item: item.model.id)
    non_api_options.sort(key=lambda item: (item.model_name, item.access_type))
    return AdaptedPipelineOutput(route_models=adapted, non_api_options=non_api_options)


def _display_name(route_id: str) -> str:
    return route_id.split("/", 1)[1] if "/" in route_id else route_id


def _infer_capability_tags(canonical_route_id: str) -> list[str]:
    model_id = canonical_route_id.split("/", 1)[1] if "/" in canonical_route_id else canonical_route_id
    tags = ["chat"]
    text = model_id.lower()

    if any(token in text for token in ["gpt-4.1", "gpt-4o", "sonnet", "pro", "coder"]):
        tags.append("code")
    if any(token in text for token in ["o3", "o4", "opus", "sonnet", "pro"]):
        tags.append("reasoning")
    if any(token in text for token in ["flash", "mini", "haiku"]):
        tags.append("fast")

    return tags


def _build_description(record: VerifiedDataRecord, source_ids: list[str]) -> str:
    evidence = record.evidence
    price = record.price_snapshot
    route_label = str(price.metadata.get("route_label", record.verified.source_id)) if price else record.verified.source_id
    route_kind = str(price.metadata.get("route_kind", "route")) if price else "route"
    friction_flag = bool(price.metadata.get("friction_flag", False)) if price else False
    benefit_summary = str(price.metadata.get("benefit_summary", "")) if price else ""
    effective_cost_note = str(price.metadata.get("effective_cost_note", "")) if price else ""
    observed_input = float(price.metadata.get("observed_input_price", price.input_price)) if price else 0.0
    observed_output = float(price.metadata.get("observed_output_price", price.output_price)) if price else 0.0
    pricing_phrase = (
        f"Effective cost with credits: {effective_cost_note}."
        if effective_cost_note
        else f"Observed route cost: ${observed_input:.3f} in / ${observed_output:.3f} out."
    )
    source_note = (
        f"Route: {route_label} ({route_kind}). Verified from {len(source_ids)} source(s); winner: {record.verified.winner_source_id}."
    )
    trust_note = f" Trust tier: {int(record.trust_tier)}. Evidence available."
    conflict_note = " Conflict detected across sources." if record.conflict_flag else " No source conflict detected."
    friction_note = " Friction flag present." if friction_flag else ""
    benefit_note = f" Benefit: {benefit_summary}." if benefit_summary else ""
    return f"{evidence.excerpt} {source_note} {pricing_phrase}{benefit_note}{trust_note}{conflict_note}{friction_note}".strip()


def _confidence_for_route(
    *,
    trust_tier: int,
    route_kind: str,
    pricing_indirect: bool,
    conflict_flag: bool,
) -> float:
    confidence = 0.95 if trust_tier == 1 else 0.82 if trust_tier == 2 else 0.7
    if route_kind in {"gateway", "aggregator", "free_tier", "promo"}:
        confidence -= 0.08
    if pricing_indirect:
        confidence -= 0.05
    if conflict_flag:
        confidence -= 0.12
    return max(0.35, round(confidence, 2))


def _effective_value_hint(
    *,
    route_kind: str,
    benefit_summary: str,
    effective_cost_note: str,
) -> dict[str, object]:
    if effective_cost_note:
        usage_profile = "light"
        approx_requests = 25
        approx_tokens = 25000
        effective_cost_label = "effectively_free"
        note = f"Best value for the first ~{approx_requests} requests or up to ~{approx_tokens:,} tokens due to credits/quota, despite standard pricing."
        confidence = "low" if route_kind == "promo" else "medium"
    elif benefit_summary:
        usage_profile = "medium"
        approx_requests = 100
        approx_tokens = 100000
        effective_cost_label = "reduced_cost"
        note = f"Can reduce spend for roughly the first ~{approx_requests} requests or up to ~{approx_tokens:,} tokens while provider pricing stays standard."
        confidence = "medium"
    else:
        usage_profile = "heavy"
        approx_requests = 0
        approx_tokens = 0
        effective_cost_label = "standard_cost"
        note = "Provider pricing applies directly; no route benefit reduces the cost."
        confidence = "high" if route_kind == "official" else "medium"

    if route_kind in {"promo", "free_tier"} and effective_cost_note:
        usage_profile = "light"
        if route_kind == "promo":
            confidence = "low"

    return {
        "usage_profile": usage_profile,
        "approx_requests": approx_requests,
        "approx_tokens": approx_tokens,
        "effective_cost_label": effective_cost_label,
        "note": note,
        "confidence": confidence,
    }


def _not_included_reason(*, access_type: str) -> str:
    if access_type == "platform_ui":
        return "not available via API"
    return "no comparable pricing"
