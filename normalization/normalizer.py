"""
Evidence-backed normalization step.
"""

from __future__ import annotations

import uuid

from normalization.canonical import canonicalize_model_name, canonicalize_provider_id, canonicalize_route
from models.token import NormalizedToken, Offer, PriceSnapshot, RawToken, SourceEvidence


class TokenNormalizer:
    def normalize(self, raw: RawToken, evidence: SourceEvidence) -> NormalizedToken:
        if not evidence.id:
            raise ValueError("no normalized data without evidence")

        value = self._apply_rules(raw.value)
        entity_type = raw.metadata.get("entity_type", "offer")
        metadata = dict(raw.metadata)

        if entity_type == "price_snapshot":
            provider_id = canonicalize_provider_id(str(metadata.get("provider_id", "")))
            source_model_name = str(
                metadata.get("source_model_name")
                or metadata.get("model_name")
                or metadata.get("route_id")
                or raw.value
            )
            canonical_route = canonicalize_route(
                provider_id or raw.value.split("/", 1)[0],
                metadata.get("canonical_route_id", metadata.get("route_id", source_model_name)),
            )
            access_route_id = str(metadata.get("route_id") or canonical_route)
            return PriceSnapshot(
                id=str(uuid.uuid4()),
                value=value,
                source=raw.source,
                raw_id=raw.id,
                evidence_id=evidence.id,
                source_id=evidence.source_id,
                trust_tier=evidence.trust_tier,
                route_id=access_route_id,
                input_price=float(metadata.get("input_price", 0.0)),
                output_price=float(metadata.get("output_price", 0.0)),
                unit=metadata.get("unit", "usd_per_1m_tokens"),
                metadata={
                    **metadata,
                    "provider_id": provider_id,
                    "source_model_name": source_model_name,
                    "canonical_model_id": canonicalize_model_name(source_model_name),
                    "canonical_route_id": canonical_route,
                    "route_id": access_route_id,
                },
            )

        return Offer(
            id=str(uuid.uuid4()),
            value=value,
            source=raw.source,
            raw_id=raw.id,
            evidence_id=evidence.id,
            source_id=evidence.source_id,
            trust_tier=evidence.trust_tier,
            offer_type=metadata.get("offer_type", "generic"),
            title=str(metadata.get("model_name") or raw.title.strip()),
            headline_value=str(metadata.get("access_description") or raw.value.strip()),
            terms_summary=metadata.get("terms_summary", raw.excerpt.strip()),
            metadata=metadata,
        )

    def normalize_batch(
        self,
        tokens: list[RawToken],
        evidence_by_raw_id: dict[str, SourceEvidence],
    ) -> list[NormalizedToken]:
        normalized: list[NormalizedToken] = []
        for token in tokens:
            evidence = evidence_by_raw_id.get(token.id)
            if evidence is None:
                raise ValueError(f"no normalized data without evidence: raw_id={token.id}")
            normalized.append(self.normalize(token, evidence))
        return normalized

    # ── Override below ────────────────────────────────────────────────────────

    def _apply_rules(self, value: str) -> str:
        return value.strip().lower()
