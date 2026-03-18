"""
Simple file-backed pricing sources for the pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ingestion.base import BaseIngestionSource
from ingestion.source_registry import SourceDefinition, SourceRegistry
from models.token import RawToken
from normalization.canonical import canonicalize_provider_id, canonicalize_route


class JsonPricingSource(BaseIngestionSource):
    def __init__(
        self,
        source_id: str,
        data_path: str | Path,
        registry: SourceRegistry | None = None,
    ) -> None:
        self.source_id = source_id
        self.data_path = Path(data_path)
        self.registry = registry or SourceRegistry()

    def fetch(self) -> list[RawToken]:
        definition = self.registry.get(self.source_id)
        payload = self._load()
        captured_at = datetime.fromisoformat(payload["captured_at"])
        parser_version = str(payload["parser_version"])
        return [
            self._to_raw_token(item, definition, captured_at, parser_version)
            for item in payload.get("items", [])
        ]

    def _load(self) -> dict[str, object]:
        with self.data_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _to_raw_token(
        self,
        item: dict[str, object],
        definition: SourceDefinition,
        captured_at: datetime,
        parser_version: str,
    ) -> RawToken:
        entity_type = str(item.get("entity_type", "price_snapshot"))
        if entity_type == "offer":
            return self._to_offer_token(item, definition, captured_at, parser_version)

        provider_id = canonicalize_provider_id(str(item.get("provider_id", "")))
        source_model_name = str(item.get("model_name") or item.get("route_id") or "")
        canonical_route_id = canonicalize_route(
            provider_id or str(item.get("route_id", "")).split("/", 1)[0],
            str(item.get("route_id") or source_model_name),
        )
        route_variant = str(item.get("route_variant") or definition.id)
        route_kind = str(item.get("route_kind") or _default_route_kind(definition.id))
        route_label = str(item.get("route_label") or _default_route_label(definition.name, route_kind))
        access_route_id = f"{canonical_route_id}::{route_variant}"
        input_price = float(item["input_price"])
        output_price = float(item["output_price"])
        title = str(item.get("title", canonical_route_id))
        excerpt = str(
            item.get(
                "excerpt",
                f"Input ${input_price:.4f} / Output ${output_price:.4f} per 1M tokens",
            )
        )
        return RawToken(
            id=str(uuid4()),
            value=canonical_route_id,
            source=definition.name,
            source_id=definition.id,
            url=str(item["url"]),
            title=title,
            excerpt=excerpt,
            captured_at=captured_at,
            parser_version=parser_version,
            trust_tier=definition.trust_tier,
            metadata={
                "entity_type": "price_snapshot",
                "access_type": str(item.get("access_type", "api")),
                "route_id": access_route_id,
                "canonical_route_id": canonical_route_id,
                "provider_id": provider_id or canonical_route_id.split("/")[0],
                "model_id": access_route_id,
                "source_model_name": source_model_name or canonical_route_id.split("/", 1)[1],
                "route_variant": route_variant,
                "route_kind": route_kind,
                "route_label": route_label,
                "availability": bool(item.get("availability", True)),
                "friction_flag": bool(item.get("friction_flag", route_kind in {"gateway", "free_tier", "promo"})),
                "observed_input_price": float(item.get("observed_input_price", input_price)),
                "observed_output_price": float(item.get("observed_output_price", output_price)),
                "benefit_type": str(item.get("benefit_type", "")),
                "benefit_summary": str(item.get("benefit_summary", "")),
                "effective_cost_note": str(item.get("effective_cost_note", "")),
                "pricing_indirect": bool(item.get("pricing_indirect", definition.trust_tier > 1)),
                "input_price": input_price,
                "output_price": output_price,
                "source_name": definition.name,
                "source_type": definition.source_type,
                "owner": definition.owner,
            },
        )

    def _to_offer_token(
        self,
        item: dict[str, object],
        definition: SourceDefinition,
        captured_at: datetime,
        parser_version: str,
    ) -> RawToken:
        model_name = str(item.get("model_name", "")).strip()
        access_type = str(item.get("access_type", "platform_ui"))
        title = str(item.get("title", model_name or definition.name))
        excerpt = str(item.get("excerpt", item.get("notes", "")))
        return RawToken(
            id=str(uuid4()),
            value=model_name or title,
            source=definition.name,
            source_id=definition.id,
            url=str(item["url"]),
            title=title,
            excerpt=excerpt,
            captured_at=captured_at,
            parser_version=parser_version,
            trust_tier=definition.trust_tier,
            metadata={
                "entity_type": "offer",
                "access_type": access_type,
                "model_name": model_name,
                "offer_type": str(item.get("offer_type", "alternative_access")),
                "access_description": str(item.get("access_description", excerpt)),
                "usage_limits": str(item.get("usage_limits", "")),
                "notes": str(item.get("notes", "")),
                "source_name": definition.name,
                "source_type": definition.source_type,
                "owner": definition.owner,
            },
        )


class OpenAIOfficialPricingSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/openai_official_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="openai_official_pricing",
            data_path=data_path,
            registry=registry,
        )


class AnthropicOfficialPricingSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/anthropic_official_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="anthropic_official_pricing",
            data_path=data_path,
            registry=registry,
        )


class GoogleAIOfficialPricingSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/google_ai_official_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="google_ai_official_pricing",
            data_path=data_path,
            registry=registry,
        )


class GroqOfficialPricingSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/groq_official_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="groq_official_pricing",
            data_path=data_path,
            registry=registry,
        )


class OpenRouterCatalogSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/openrouter_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="openrouter_catalog",
            data_path=data_path,
            registry=registry,
        )


class ArtificialAnalysisCatalogSource(JsonPricingSource):
    def __init__(
        self,
        data_path: str | Path = "data/artificial_analysis_pricing.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        super().__init__(
            source_id="artificial_analysis_catalog",
            data_path=data_path,
            registry=registry,
        )


class LocalModelsSource(BaseIngestionSource):
    def __init__(
        self,
        data_path: str | Path = "data/models.json",
        registry: SourceRegistry | None = None,
    ) -> None:
        self.source_id = "local_models_catalog"
        self.data_path = Path(data_path)
        self.registry = registry or SourceRegistry()

    def fetch(self) -> list[RawToken]:
        definition = self.registry.get(self.source_id)
        with self.data_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        captured_at = datetime.utcfromtimestamp(self.data_path.stat().st_mtime)
        parser_version = "local-models-v1"
        tokens: list[RawToken] = []
        for item in payload:
            model_id = str(item.get("id", "")).strip()
            if not model_id:
                continue
            provider_hint, _, model_hint = model_id.partition("/")
            provider_id = canonicalize_provider_id(provider_hint or str(item.get("provider", "")))
            source_model_name = model_hint or str(item.get("name", "")).strip() or model_id
            canonical_route_id = canonicalize_route(provider_id or provider_hint, model_id)
            input_price = float(item.get("input", 0.0))
            output_price = float(item.get("output", 0.0))
            is_free = bool(item.get("is_free", False))
            title = str(item.get("name") or canonical_route_id)
            excerpt = (
                "OpenRouter local dataset marks this model as free."
                if is_free
                else f"Input ${input_price:.4f} / Output ${output_price:.4f} per 1M tokens"
            )
            tokens.append(
                RawToken(
                    id=str(uuid4()),
                    value=canonical_route_id,
                    source=definition.name,
                    source_id=definition.id,
                    url=f"https://openrouter.ai/{model_id}",
                    title=title,
                    excerpt=excerpt,
                    captured_at=captured_at,
                    parser_version=parser_version,
                    trust_tier=definition.trust_tier,
                    metadata={
                        "entity_type": "price_snapshot",
                        "access_type": "api",
                        "route_id": f"{canonical_route_id}::openrouter-local",
                        "canonical_route_id": canonical_route_id,
                        "provider_id": provider_id or canonical_route_id.split("/")[0],
                        "model_id": f"{canonical_route_id}::openrouter-local",
                        "source_model_name": source_model_name,
                        "route_variant": "openrouter-local",
                        "route_kind": "gateway",
                        "route_label": "OpenRouter local dataset",
                        "availability": True,
                        "friction_flag": is_free,
                        "observed_input_price": input_price,
                        "observed_output_price": output_price,
                        "benefit_type": "free_tier" if is_free else "",
                        "benefit_summary": "Marked free in local OpenRouter dataset." if is_free else "",
                        "effective_cost_note": "Free access path observed in local dataset." if is_free else "",
                        "pricing_indirect": True,
                        "input_price": input_price,
                        "output_price": output_price,
                        "source_name": definition.name,
                        "source_type": definition.source_type,
                        "owner": definition.owner,
                        "tags": list(item.get("tags", [])),
                    },
                )
            )
        return tokens


def build_default_sources(registry: SourceRegistry | None = None) -> list[BaseIngestionSource]:
    return [
        OpenAIOfficialPricingSource(registry=registry),
        AnthropicOfficialPricingSource(registry=registry),
        GoogleAIOfficialPricingSource(registry=registry),
        GroqOfficialPricingSource(registry=registry),
        OpenRouterCatalogSource(registry=registry),
        ArtificialAnalysisCatalogSource(registry=registry),
        LocalModelsSource(registry=registry),
    ]


def _default_route_kind(source_id: str) -> str:
    if source_id.endswith("official_pricing"):
        return "official"
    if source_id == "openrouter_catalog":
        return "gateway"
    return "aggregator"


def _default_route_label(source_name: str, route_kind: str) -> str:
    return f"{source_name} {route_kind.replace('_', ' ')}".strip()
