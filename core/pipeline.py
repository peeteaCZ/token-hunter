"""
Main pipeline: parsing -> evidence -> normalization -> conflict-aware verification -> storage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ingestion.base import BaseIngestionSource
from ingestion.file_sources import build_default_sources
from models.token import Offer, PriceSnapshot, SourceEvidence, TrustTier, VerifiedToken
from normalization.normalizer import TokenNormalizer
from storage.evidence import EvidenceStorage
from storage.repository import TokenRepository
from verification.verifier import TokenVerifier

logger = logging.getLogger(__name__)


@dataclass
class VerifiedDataRecord:
    price_snapshot: PriceSnapshot | None
    offer: Offer | None
    evidence: SourceEvidence
    trust_tier: TrustTier
    conflict_flag: bool
    verified: VerifiedToken


@dataclass
class PipelineExecutionResult:
    stats: dict[str, Any]
    records: list[VerifiedDataRecord]


class Pipeline:
    def __init__(
        self,
        sources: list[BaseIngestionSource],
        normalizer: TokenNormalizer | None = None,
        verifier: TokenVerifier | None = None,
        repository: TokenRepository | None = None,
        evidence_storage: EvidenceStorage | None = None,
    ) -> None:
        self.sources = sources
        self.normalizer = normalizer or TokenNormalizer()
        self.verifier = verifier or TokenVerifier()
        self.repository = repository or TokenRepository()
        self.evidence_storage = evidence_storage or EvidenceStorage()

    def run(self) -> dict[str, Any]:
        return self.execute().stats

    def execute(self) -> PipelineExecutionResult:
        raw_total = 0
        evidence_total = 0
        normalized_total = 0
        verified_total = 0
        sources_used: set[str] = set()
        all_normalized = []
        source_item_counts: dict[str, int] = {}

        for source in self.sources:
            logger.info("ingesting from %s", source)
            raw = source.fetch()
            raw_total += len(raw)
            sources_used.add(source.source_id)
            source_item_counts[source.source_id] = len(raw)
            logger.info("source %s produced %d items", source.source_id, len(raw))

            evidence_by_raw_id = {}
            for item in raw:
                evidence = self.evidence_storage.save_evidence(item)
                evidence_by_raw_id[item.id] = evidence
                evidence_total += 1

            normalized = self.normalizer.normalize_batch(raw, evidence_by_raw_id)
            all_normalized.extend(normalized)
            normalized_total += len(normalized)

        verified = self.verifier.verify_batch(all_normalized)
        verified_total += len(verified)
        self.repository.save_batch(verified)
        summaries = self.verifier.summarize(all_normalized)
        conflicts_detected = sum(1 for item in summaries if item["conflict_flag"])
        matched_entities = sum(1 for item in summaries if int(item["source_count"]) > 1)
        unmatched_entities = len(summaries) - matched_entities
        records = self._build_verified_records(all_normalized, verified)

        logger.info(
            "pipeline complete  raw=%d  evidence=%d  normalized=%d  verified=%d  sources=%d  conflicts=%d  matched=%d  unmatched=%d",
            raw_total,
            evidence_total,
            normalized_total,
            verified_total,
            len(sources_used),
            conflicts_detected,
            matched_entities,
            unmatched_entities,
        )
        stats = {
            "raw": raw_total,
            "evidence": evidence_total,
            "normalized": normalized_total,
            "verified": verified_total,
            "sources_used": len(sources_used),
            "source_item_counts": source_item_counts,
            "conflicts_detected": conflicts_detected,
            "matched_entities": matched_entities,
            "unmatched_entities": unmatched_entities,
            "entities": summaries,
        }
        return PipelineExecutionResult(stats=stats, records=records)

    def _build_verified_records(
        self,
        normalized: list[PriceSnapshot | Offer],
        verified: list[VerifiedToken],
    ) -> list[VerifiedDataRecord]:
        verified_by_normalized_id = {item.normalized_id: item for item in verified}
        records: list[VerifiedDataRecord] = []

        for entity in normalized:
            verified_item = verified_by_normalized_id[entity.id]
            evidence = self.evidence_storage.get_evidence_by_id(entity.evidence_id)
            if evidence is None:
                raise ValueError(f"missing evidence for normalized entity: {entity.id}")

            records.append(
                VerifiedDataRecord(
                    price_snapshot=entity if isinstance(entity, PriceSnapshot) else None,
                    offer=entity if isinstance(entity, Offer) else None,
                    evidence=evidence,
                    trust_tier=verified_item.trust_tier,
                    conflict_flag=verified_item.conflict_flag,
                    verified=verified_item,
                )
            )

        return records


def get_verified_data(
    *,
    sources: list[BaseIngestionSource] | None = None,
    evidence_path: str = "data/evidence.jsonl",
) -> list[VerifiedDataRecord]:
    pipeline = Pipeline(
        sources=sources or build_default_sources(),
        repository=TokenRepository(),
        evidence_storage=EvidenceStorage(evidence_path),
    )
    return pipeline.execute().records
