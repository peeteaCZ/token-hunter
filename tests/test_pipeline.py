"""Tests for the expanded multi-source pricing pipeline."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from core.pipeline import Pipeline
from ingestion.file_sources import (
    AnthropicOfficialPricingSource,
    OpenAIOfficialPricingSource,
    OpenRouterCatalogSource,
    build_default_sources,
)
from ingestion.source_registry import SourceRegistry
from models.token import PriceSnapshot, RawToken, SourceEvidence, TrustTier
from normalization.canonical import canonicalize_route
from normalization.normalizer import TokenNormalizer
from storage.evidence import EvidenceStorage
from storage.repository import TokenRepository


def _write_snapshot(
    path,
    *,
    provider_id: str,
    model_name: str,
    input_price: float,
    output_price: float,
    url: str,
) -> None:
    path.write_text(
        json.dumps(
            {
                "captured_at": "2026-03-18T00:00:00",
                "parser_version": "test-snapshot-v1",
                "items": [
                    {
                        "provider_id": provider_id,
                        "model_name": model_name,
                        "input_price": input_price,
                        "output_price": output_price,
                        "url": url,
                        "title": "Pricing",
                        "excerpt": "Snapshot pricing",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_source_registry_contains_five_high_quality_sources() -> None:
    registry = SourceRegistry()
    definitions = {definition.id: definition for definition in registry.all()}

    assert len(definitions) == 5
    assert definitions["openai_official_pricing"].trust_tier == TrustTier.TIER_1
    assert definitions["anthropic_official_pricing"].trust_tier == TrustTier.TIER_1
    assert definitions["google_ai_official_pricing"].trust_tier == TrustTier.TIER_1
    assert definitions["openrouter_catalog"].trust_tier == TrustTier.TIER_2
    assert definitions["artificial_analysis_catalog"].trust_tier == TrustTier.TIER_2


def test_canonical_matcher_handles_model_variants() -> None:
    assert canonicalize_route("openai", "GPT-4o Mini") == "openai/gpt-4o-mini"
    assert canonicalize_route("openai", "gpt-4o-mini") == "openai/gpt-4o-mini"
    assert canonicalize_route("anthropic", "Claude-3-Haiku-20240307") == "anthropic/claude-3-haiku"
    assert canonicalize_route("anthropic", "Claude 3 Haiku") == "anthropic/claude-3-haiku"


def test_normalizer_requires_saved_evidence() -> None:
    normalizer = TokenNormalizer()
    raw = RawToken(
        id="x",
        value="GPT-4o Mini",
        source="test",
        source_id="openai_official_pricing",
        url="https://example.com/pricing",
        title="Pricing",
        excerpt="Pricing excerpt",
        captured_at=datetime.utcnow(),
        parser_version="test-parser-v1",
        trust_tier=TrustTier.TIER_1,
        metadata={
            "entity_type": "price_snapshot",
            "provider_id": "openai",
            "model_name": "GPT-4o Mini",
        },
    )
    evidence = SourceEvidence(
        id="",
        source_id=raw.source_id,
        url=raw.url,
        title=raw.title,
        excerpt=raw.excerpt,
        captured_at=raw.captured_at,
        parser_version=raw.parser_version,
        trust_tier=TrustTier.TIER_1,
        last_verified=raw.captured_at,
    )

    with pytest.raises(ValueError, match="no normalized data without evidence"):
        normalizer.normalize(raw, evidence)


def test_two_sources_normalize_variants_into_same_price_snapshot(tmp_path) -> None:
    official_path = tmp_path / "openai.json"
    catalog_path = tmp_path / "openrouter.json"
    _write_snapshot(
        official_path,
        provider_id="openai",
        model_name="GPT-4o Mini",
        input_price=0.15,
        output_price=0.60,
        url="https://openai.com/api/pricing/",
    )
    _write_snapshot(
        catalog_path,
        provider_id="openai",
        model_name="gpt-4o-mini",
        input_price=0.16,
        output_price=0.65,
        url="https://openrouter.ai/openai/gpt-4o-mini",
    )

    official_source = OpenAIOfficialPricingSource(data_path=official_path)
    catalog_source = OpenRouterCatalogSource(data_path=catalog_path)
    evidence_storage = EvidenceStorage(tmp_path / "evidence.jsonl")
    normalizer = TokenNormalizer()

    normalized = []
    for source in [official_source, catalog_source]:
        raw_items = source.fetch()
        evidence_by_raw_id = {
            item.id: evidence_storage.save_evidence(item) for item in raw_items
        }
        normalized.extend(normalizer.normalize_batch(raw_items, evidence_by_raw_id))

    assert len(normalized) == 2
    assert all(isinstance(item, PriceSnapshot) for item in normalized)
    assert {item.route_id for item in normalized} == {"openai/gpt-4o-mini"}
    assert {int(item.trust_tier) for item in normalized} == {1, 2}


def test_anthropic_variants_match_to_same_canonical_route(tmp_path) -> None:
    official_path = tmp_path / "anthropic.json"
    catalog_path = tmp_path / "catalog.json"
    _write_snapshot(
        official_path,
        provider_id="anthropic",
        model_name="Claude 3 Haiku",
        input_price=0.25,
        output_price=1.25,
        url="https://www.anthropic.com/pricing",
    )
    _write_snapshot(
        catalog_path,
        provider_id="anthropic",
        model_name="Claude-3-Haiku-20240307",
        input_price=0.27,
        output_price=1.29,
        url="https://openrouter.ai/anthropic/claude-3-haiku",
    )

    official_source = AnthropicOfficialPricingSource(data_path=official_path)
    catalog_source = OpenRouterCatalogSource(data_path=catalog_path)
    evidence_storage = EvidenceStorage(tmp_path / "evidence.jsonl")
    normalizer = TokenNormalizer()

    normalized = []
    for source in [official_source, catalog_source]:
        raw_items = source.fetch()
        evidence_by_raw_id = {
            item.id: evidence_storage.save_evidence(item) for item in raw_items
        }
        normalized.extend(normalizer.normalize_batch(raw_items, evidence_by_raw_id))

    assert {item.route_id for item in normalized} == {"anthropic/claude-3-haiku"}


def test_pipeline_builds_meaningful_multi_source_dataset(tmp_path) -> None:
    repo = TokenRepository()
    result = Pipeline(
        sources=build_default_sources(),
        repository=repo,
        evidence_storage=EvidenceStorage(tmp_path / "evidence.jsonl"),
    ).execute()

    stats = result.stats

    assert stats["sources_used"] == 5
    assert 20 <= stats["normalized"] <= 50
    assert stats["normalized"] == 36
    assert stats["verified"] == 36
    assert stats["source_item_counts"] == {
        "openai_official_pricing": 6,
        "anthropic_official_pricing": 5,
        "google_ai_official_pricing": 5,
        "openrouter_catalog": 10,
        "artificial_analysis_catalog": 10,
    }
    assert stats["matched_entities"] == 14
    assert stats["unmatched_entities"] == 2
    assert repo.count() == 36


def test_pipeline_detects_conflicts_and_consistency(tmp_path) -> None:
    repo = TokenRepository()
    result = Pipeline(
        sources=build_default_sources(),
        repository=repo,
        evidence_storage=EvidenceStorage(tmp_path / "evidence.jsonl"),
    ).execute()
    entities = {item["entity_key"]: item for item in result.stats["entities"]}

    assert entities["price_snapshot:openai/gpt-4o-mini"]["conflict_flag"] is True
    assert entities["price_snapshot:openai/o4-mini"]["conflict_flag"] is False
    assert entities["price_snapshot:anthropic/claude-3-haiku"]["source_count"] == 3
    assert entities["price_snapshot:google/gemini-2.5-pro"]["winner_source_id"] == "google_ai_official_pricing"
