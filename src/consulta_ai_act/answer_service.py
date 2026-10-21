"""Application service combining retrieval, generation, and citation validation."""

from __future__ import annotations

from typing import Protocol

from consulta_ai_act.generation.answer_generator import ABSTENTION_TEXT
from consulta_ai_act.models import Answer, Evidence, RetrievedChunk


class Retriever(Protocol):
    def retrieve(self, question: str, *, k: int | None = None) -> list[RetrievedChunk]: ...


class Generator(Protocol):
    def generate(self, question: str, evidence: list[RetrievedChunk]) -> str: ...


class CitationChecker(Protocol):
    def validate(self, answer: str, evidence: list[RetrievedChunk]) -> tuple[str, ...]: ...


class AnswerService:
    """Return only generated claims whose citations match retrieved passages."""

    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        citation_validator: CitationChecker,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.citation_validator = citation_validator

    def ask(self, question: str, *, k: int | None = None) -> Answer:
        retrieved = self.retriever.retrieve(question, k=k)
        if not retrieved:
            return Answer(answer=ABSTENTION_TEXT, abstained=True)

        generated = self.generator.generate(question, retrieved).strip()
        references = self.citation_validator.validate(generated, retrieved)
        if generated == ABSTENTION_TEXT:
            return Answer(answer=ABSTENTION_TEXT, abstained=True)

        evidence_by_reference: dict[str, list[RetrievedChunk]] = {}
        for item in retrieved:
            evidence_by_reference.setdefault(item.chunk.canonical_reference, []).append(item)
        evidence = tuple(
            Evidence(
                reference=reference,
                text=item.chunk.text,
                chunk_id=item.chunk.chunk_id,
            )
            for reference in references
            for item in evidence_by_reference.get(reference, [])
        )
        if not evidence:
            raise ValueError("Validated references did not resolve to retrieved evidence")
        return Answer(answer=generated, references=references, evidence=evidence)
