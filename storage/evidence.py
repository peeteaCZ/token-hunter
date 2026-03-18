"""
File-based storage for evidence snapshots.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from models.token import RawToken, SourceEvidence, TrustTier


class EvidenceStorage:
    def __init__(self, path: str | Path = "data/evidence.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, SourceEvidence] = {}
        self._load()

    def save_evidence(self, item: RawToken) -> SourceEvidence:
        evidence = SourceEvidence(
            id=str(uuid.uuid4()),
            source_id=item.source_id,
            url=item.url,
            title=item.title,
            excerpt=item.excerpt,
            captured_at=item.captured_at,
            parser_version=item.parser_version,
            trust_tier=TrustTier(int(item.trust_tier)),
            last_verified=item.captured_at,
            metadata={"raw_id": item.id, "source": item.source, **dict(item.metadata)},
        )
        self._append(evidence)
        self._index[evidence.id] = evidence
        return evidence

    def get_evidence_by_id(self, evidence_id: str) -> SourceEvidence | None:
        return self._index.get(evidence_id)

    def count(self) -> int:
        return len(self._index)

    def _load(self) -> None:
        if not self.path.exists():
            return

        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = line.strip()
                if not payload:
                    continue
                evidence = self._deserialize(json.loads(payload))
                self._index[evidence.id] = evidence

    def _append(self, evidence: SourceEvidence) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self._serialize(evidence), ensure_ascii=True))
            handle.write("\n")

    def _serialize(self, evidence: SourceEvidence) -> dict[str, object]:
        payload = asdict(evidence)
        payload["captured_at"] = evidence.captured_at.isoformat()
        payload["last_verified"] = evidence.last_verified.isoformat()
        payload["trust_tier"] = int(evidence.trust_tier)
        return payload

    def _deserialize(self, payload: dict[str, object]) -> SourceEvidence:
        return SourceEvidence(
            id=str(payload["id"]),
            source_id=str(payload["source_id"]),
            url=str(payload["url"]),
            title=str(payload["title"]),
            excerpt=str(payload["excerpt"]),
            captured_at=datetime.fromisoformat(str(payload["captured_at"])),
            parser_version=str(payload["parser_version"]),
            trust_tier=TrustTier(int(payload["trust_tier"])),
            last_verified=datetime.fromisoformat(str(payload["last_verified"])),
            metadata=dict(payload.get("metadata", {})),
        )
