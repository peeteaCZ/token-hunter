"""
Core pipeline domain models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from enum import IntEnum
from typing import Any


class RiskLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrustTier(IntEnum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


@dataclass
class RawToken:
    """Parsed item captured from a source before evidence is persisted."""

    id: str
    value: str
    source: str
    source_id: str = ""
    url: str = ""
    title: str = ""
    excerpt: str = ""
    captured_at: datetime = field(default_factory=datetime.utcnow)
    parser_version: str = "v1"
    trust_tier: TrustTier | int = TrustTier.TIER_3
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id:
            self.source_id = self.source
        if not self.title:
            self.title = self.value.strip()
        if not self.excerpt:
            self.excerpt = self.value.strip()
        if not isinstance(self.trust_tier, TrustTier):
            self.trust_tier = TrustTier(int(self.trust_tier))


@dataclass
class SourceEvidence:
    """Persisted evidence snapshot aligned with SOURCE_POLICY requirements."""

    id: str
    source_id: str
    url: str
    title: str
    excerpt: str
    captured_at: datetime
    parser_version: str
    trust_tier: TrustTier
    last_verified: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedToken:
    """Base normalized entity that must always point to saved evidence."""

    id: str
    value: str
    source: str
    normalized_at: datetime = field(default_factory=datetime.utcnow)
    raw_id: str = ""
    evidence_id: str = ""
    source_id: str = ""
    trust_tier: TrustTier = TrustTier.TIER_3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PriceSnapshot(NormalizedToken):
    route_id: str = ""
    input_price: float = 0.0
    output_price: float = 0.0
    unit: str = "usd_per_1m_tokens"
    observed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Offer(NormalizedToken):
    offer_type: str = "generic"
    title: str = ""
    headline_value: str = ""
    terms_summary: str = ""


@dataclass
class VerifiedToken:
    """Verified entity with a risk assessment attached."""

    id: str
    value: str
    source: str
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    verified_at: datetime = field(default_factory=datetime.utcnow)
    normalized_id: str = ""
    evidence_id: str = ""
    source_id: str = ""
    trust_tier: TrustTier = TrustTier.TIER_3
    conflict_flag: bool = False
    source_count: int = 1
    source_ids: list[str] = field(default_factory=list)
    winner_source_id: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
