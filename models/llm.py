"""
LLM pricing domain models.
Pure dataclasses — no ORM or framework coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PricingInfo:
    input_per_1m: float    # USD per 1 million input tokens
    output_per_1m: float   # USD per 1 million output tokens
    is_free: bool = False


@dataclass
class ModelEntry:
    """A single LLM model with its pricing and metadata."""

    id: str                  # e.g. "openai/gpt-4o-mini"
    name: str                # display name
    provider_id: str         # e.g. "openai"
    provider_name: str       # e.g. "OpenAI"
    pricing: PricingInfo
    context_length: int = 0
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "openrouter"
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_free(self) -> bool:
        return self.pricing.is_free

    @property
    def combined_price(self) -> float:
        """Weighted combined cost per 1M tokens.

        Uses a 1-input : 2-output token ratio as a typical session proxy.
        Returns 0.0 for free models.
        """
        if self.is_free:
            return 0.0
        return (self.pricing.input_per_1m + self.pricing.output_per_1m * 2) / 3

    @property
    def openrouter_url(self) -> str:
        return f"https://openrouter.ai/{self.id}"


@dataclass
class DealCard:
    """A scored model entry ready for display in the UI."""

    model: ModelEntry
    score: float
    use_case: str
    rank: int
    headline: str
    why: str
    caveats: list[str] = field(default_factory=list)
    savings_label: str = ""


@dataclass
class RadarSnapshot:
    """Aggregated view of the current market — used by the home page."""

    generated_at: datetime
    free_models: list[DealCard]
    cheapest_models: list[DealCard]
    best_coding: list[DealCard]
    best_chat: list[DealCard]
    total_models: int
    free_count: int


@dataclass
class NonApiOption:
    model_name: str
    access_type: str
    access_description: str
    usage_limits: str = ""
    notes: str = ""
    source: str = ""
    not_included_reason: str = ""
