"""
Abstract base for all ingestion sources.
Each source implements `fetch()` and returns parsed items with evidence metadata.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.token import RawToken


class BaseIngestionSource(ABC):
    source_id: str = ""

    @abstractmethod
    def fetch(self) -> list[RawToken]:
        """Pull tokens from the source and return them as RawTokens."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source_id={self.source_id!r})"
