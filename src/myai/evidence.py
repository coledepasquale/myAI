from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from myai.domain import Evidence


class EvidenceStore:
    """In-memory evidence registry for the POC.

    The interface is intentionally small so persistence can later move to SQLite,
    Postgres, or a graph store without leaking storage concerns into reasoning code.
    """

    def __init__(self, evidence: Iterable[Evidence] = ()) -> None:
        self._items: dict[UUID, Evidence] = {}
        self.add_many(evidence)

    def add(self, item: Evidence) -> None:
        if item.id in self._items:
            raise ValueError(f"duplicate evidence id: {item.id}")
        self._items[item.id] = item

    def add_many(self, items: Iterable[Evidence]) -> None:
        for item in items:
            self.add(item)

    def get(self, evidence_id: UUID) -> Evidence:
        try:
            return self._items[evidence_id]
        except KeyError as exc:
            raise KeyError(f"unknown evidence id: {evidence_id}") from exc

    def resolve(self, evidence_ids: Iterable[UUID]) -> list[Evidence]:
        return [self.get(evidence_id) for evidence_id in evidence_ids]

    def all(self) -> list[Evidence]:
        return list(self._items.values())
