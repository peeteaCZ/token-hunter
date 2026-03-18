"""
In-memory storage stub.
Replace with a real DB-backed implementation without changing the interface.
"""

from __future__ import annotations

from models.token import VerifiedToken


class TokenRepository:
    def __init__(self) -> None:
        self._store: dict[str, VerifiedToken] = {}

    def save(self, token: VerifiedToken) -> None:
        self._store[token.id] = token

    def save_batch(self, tokens: list[VerifiedToken]) -> None:
        for t in tokens:
            self.save(t)

    def get(self, token_id: str) -> VerifiedToken | None:
        return self._store.get(token_id)

    def all(self) -> list[VerifiedToken]:
        return list(self._store.values())

    def count(self) -> int:
        return len(self._store)
