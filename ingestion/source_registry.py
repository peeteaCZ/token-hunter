"""
Source registry with SOURCE_POLICY-aligned trust tiers.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.token import TrustTier


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    name: str
    source_type: str
    trust_tier: TrustTier
    owner: str
    parser_type: str


class SourceRegistry:
    def __init__(self, definitions: list[SourceDefinition] | None = None) -> None:
        self._definitions = {
            definition.id: definition for definition in (definitions or default_source_definitions())
        }

    def get(self, source_id: str) -> SourceDefinition:
        return self._definitions[source_id]

    def all(self) -> list[SourceDefinition]:
        return list(self._definitions.values())


def default_source_definitions() -> list[SourceDefinition]:
    return [
        SourceDefinition(
            id="openai_official_pricing",
            name="OpenAI Official Pricing",
            source_type="official_pricing_page",
            trust_tier=TrustTier.TIER_1,
            owner="OpenAI",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="anthropic_official_pricing",
            name="Anthropic Official Pricing",
            source_type="official_pricing_page",
            trust_tier=TrustTier.TIER_1,
            owner="Anthropic",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="google_ai_official_pricing",
            name="Google AI Official Pricing",
            source_type="official_pricing_page",
            trust_tier=TrustTier.TIER_1,
            owner="Google",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="groq_official_pricing",
            name="Groq Official Pricing",
            source_type="official_pricing_page",
            trust_tier=TrustTier.TIER_1,
            owner="Groq",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="openrouter_catalog",
            name="OpenRouter Catalog",
            source_type="catalog",
            trust_tier=TrustTier.TIER_2,
            owner="OpenRouter",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="artificial_analysis_catalog",
            name="Artificial Analysis Catalog",
            source_type="catalog",
            trust_tier=TrustTier.TIER_2,
            owner="Artificial Analysis",
            parser_type="json_snapshot",
        ),
        SourceDefinition(
            id="local_models_catalog",
            name="Local Models Catalog",
            source_type="catalog",
            trust_tier=TrustTier.TIER_3,
            owner="Local",
            parser_type="json_snapshot",
        ),
    ]
