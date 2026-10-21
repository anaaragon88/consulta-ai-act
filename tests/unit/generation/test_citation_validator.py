"""Tests for deterministic citation validation against retrieved passages."""

import pytest

from consulta_ai_act.errors import CitationValidationError
from consulta_ai_act.generation.citation_validator import validate_citations
from consulta_ai_act.models import RegulationChunk, RetrievedChunk


def _retrieved(reference: str, number: str) -> RetrievedChunk:
    chunk = RegulationChunk(
        chunk_id=f"chunk-{number}",
        source_id="source-1",
        unit_type="articulo",
        unit_number=number,
        text="Texto legal exacto.",
        canonical_reference=reference,
        content_hash=f"hash-{number}",
    )
    return RetrievedChunk(chunk=chunk, score=0.8)


def test_validator_accepts_supported_article_recital_and_annex_citations() -> None:
    evidence = [
        _retrieved("[Artículo 6]", "6"),
        _retrieved("[Considerando 12]", "12"),
        _retrieved("[Anexo III]", "III"),
    ]

    citations = validate_citations(
        "Se aplica [Artículo 6], según [Considerando 12] y [Anexo III].",
        evidence,
    )

    assert citations == ("[Artículo 6]", "[Considerando 12]", "[Anexo III]")


def test_validator_rejects_citations_not_in_retrieved_evidence() -> None:
    with pytest.raises(CitationValidationError):
        validate_citations("Esto se regula en [Artículo 99].", [_retrieved("[Artículo 6]", "6")])


def test_validator_requires_citation_for_substantive_answers() -> None:
    with pytest.raises(CitationValidationError):
        validate_citations("El Reglamento impone una obligación.", [_retrieved("[Artículo 6]", "6")])


def test_validator_allows_only_exact_fixed_abstention_without_citation() -> None:
    assert validate_citations("No encuentro información suficiente en el Reglamento.", []) == ()