"""Shared domain types for regulation sources, evidence, and responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

UnitType = Literal["articulo", "considerando", "anexo"]


@dataclass(frozen=True, slots=True)
class RegulationSource:
    """Immutable provenance for an official regulation file."""

    source_id: str
    celex_id: str
    source_url: str
    language: str
    source_hash: str
    document_title: str
    retrieved_at: str | None = None


@dataclass(frozen=True, slots=True)
class RegulationChunk:
    """Exact legal text with canonical citation and unique chunk identity."""

    chunk_id: str
    source_id: str
    unit_type: UnitType
    unit_number: str
    text: str
    canonical_reference: str
    content_hash: str
    unit_title: str | None = None
    paragraph_number: str | None = None
    chunk_index: int = 0

    def __post_init__(self) -> None:
        if not self.chunk_id.strip():
            raise ValueError("chunk_id must not be empty")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.unit_number.strip():
            raise ValueError("unit_number must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")
        if not self.canonical_reference.strip():
            raise ValueError("canonical_reference must not be empty")
        if self.chunk_index < 0:
            raise ValueError("chunk_index must not be negative")


@dataclass(frozen=True, slots=True)
class Evidence:
    """A retrieved exact passage and its citation."""

    reference: str
    text: str
    chunk_id: str


@dataclass(frozen=True, slots=True)
class Answer:
    """A user-facing answer and the evidence that supports it."""

    answer: str
    references: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    disclaimer: str = "Información orientativa; no constituye asesoramiento jurídico."
    abstained: bool = False


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A retrieved passage paired with its relevance score."""

    chunk: RegulationChunk
    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")