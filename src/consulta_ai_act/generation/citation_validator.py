"""Deterministic validation of generated citations against retrieved evidence."""

from __future__ import annotations

import re

from consulta_ai_act.errors import CitationValidationError
from consulta_ai_act.generation.answer_generator import ABSTENTION_TEXT
from consulta_ai_act.models import RetrievedChunk

_CITATION_PATTERN = re.compile(
    r"\[(Artículo\s+\d+|Considerando\s+\d+|Anexo\s+[IVXLCDM]+)\]",
    re.IGNORECASE,
)


def validate_citations(answer: str, evidence: list[RetrievedChunk]) -> tuple[str, ...]:
    """Return unique exact citations, rejecting unsupported or uncited claims."""
    cleaned_answer = answer.strip()
    if cleaned_answer == ABSTENTION_TEXT:
        return ()
    if not cleaned_answer:
        raise CitationValidationError("Generated response was empty")

    citations = tuple(dict.fromkeys(match.group(0) for match in _CITATION_PATTERN.finditer(cleaned_answer)))
    if not citations:
        raise CitationValidationError("Generated response contained no legal citation")

    allowed = {_normalize_reference(item.chunk.canonical_reference) for item in evidence}
    unsupported = [citation for citation in citations if _normalize_reference(citation) not in allowed]
    if unsupported:
        raise CitationValidationError("Generated response cited a passage outside retrieved evidence")
    return citations


def _normalize_reference(reference: str) -> str:
    inside = reference.strip().strip("[]")
    normalized = " ".join(inside.split()).casefold()
    return normalized


class CitationValidator:
    """Small injectable wrapper used by the answer service."""

    def validate(self, answer: str, evidence: list[RetrievedChunk]) -> tuple[str, ...]:
        return validate_citations(answer, evidence)
