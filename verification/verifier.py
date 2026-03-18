"""
Token verification step.
Applies SOURCE_POLICY conflict resolution while keeping all evidence-backed records.
"""

from __future__ import annotations

import uuid

from models.token import NormalizedToken, PriceSnapshot, RiskLevel, VerifiedToken


class TokenVerifier:
    def verify(
        self,
        token: NormalizedToken,
        conflict_flag: bool = False,
        source_count: int = 1,
        source_ids: list[str] | None = None,
        winner_source_id: str = "",
    ) -> VerifiedToken:
        risk, notes = self._assess(token)
        return VerifiedToken(
            id=str(uuid.uuid4()),
            value=token.value,
            source=token.source,
            risk_level=risk,
            normalized_id=token.id,
            evidence_id=token.evidence_id,
            source_id=token.source_id,
            trust_tier=token.trust_tier,
            conflict_flag=conflict_flag,
            source_count=source_count,
            source_ids=list(source_ids or [token.source_id]),
            winner_source_id=winner_source_id or token.source_id,
            notes=notes,
            metadata=dict(token.metadata),
        )

    def verify_batch(self, tokens: list[NormalizedToken]) -> list[VerifiedToken]:
        summaries = self._build_group_summaries(tokens)
        return [
            self.verify(
                token=t,
                conflict_flag=summaries[self._group_key(t)]["conflict_flag"],
                source_count=summaries[self._group_key(t)]["source_count"],
                source_ids=summaries[self._group_key(t)]["source_ids"],
                winner_source_id=summaries[self._group_key(t)]["winner_source_id"],
            )
            for t in tokens
        ]

    def summarize(self, tokens: list[NormalizedToken]) -> list[dict[str, object]]:
        summaries = self._build_group_summaries(tokens)
        return list(summaries.values())

    def conflict_count(self, tokens: list[NormalizedToken]) -> int:
        return sum(1 for item in self.summarize(tokens) if item["conflict_flag"])

    # ── Override below ────────────────────────────────────────────────────────

    def _assess(self, token: NormalizedToken) -> tuple[RiskLevel, str]:
        """Return (risk_level, human-readable notes). Override with real logic."""
        return RiskLevel.UNKNOWN, "not implemented"

    def _build_group_summaries(
        self,
        tokens: list[NormalizedToken],
    ) -> dict[str, dict[str, object]]:
        grouped: dict[str, list[NormalizedToken]] = {}
        for token in tokens:
            grouped.setdefault(self._group_key(token), []).append(token)

        summaries: dict[str, dict[str, object]] = {}
        for key, group in grouped.items():
            source_ids = sorted({token.source_id for token in group if token.source_id})
            winner = min(
                group,
                key=lambda token: (int(token.trust_tier), token.source_id or token.source),
            )
            conflict_flag = self._has_conflict(group)
            summaries[key] = {
                "entity_key": key,
                "entity_type": group[0].__class__.__name__,
                "source_count": len(source_ids) or 1,
                "source_ids": source_ids or [winner.source_id],
                "winner_source_id": winner.source_id,
                "conflict_flag": conflict_flag,
                "has_multiple_sources": len(source_ids) > 1,
            }
        return summaries

    def _group_key(self, token: NormalizedToken) -> str:
        if isinstance(token, PriceSnapshot):
            return f"price_snapshot:{token.route_id}"
        return f"{token.__class__.__name__.lower()}:{token.value}"

    def _has_conflict(self, group: list[NormalizedToken]) -> bool:
        if not group or not isinstance(group[0], PriceSnapshot):
            return False
        price_pairs = {
            (token.input_price, token.output_price)
            for token in group
            if isinstance(token, PriceSnapshot)
        }
        return len(price_pairs) > 1
