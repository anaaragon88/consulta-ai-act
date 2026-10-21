"""Tests for shared domain models."""

import pytest

from consulta_ai_act.models import Answer, Evidence, RegulationChunk, RegulationSource


def test_regulation_chunk_keeps_identity_separate_from_citation() -> None:
    chunk = RegulationChunk(
        chunk_id="celex-32024R1689-art-6-p-1-0",
        source_id="source-123",
        unit_type="articulo",
        unit_number="6",
        text="Texto jurídico exacto.",
        canonical_reference="[Artículo 6]",
        content_hash="content-hash",
        paragraph_number="1",
    )

    assert chunk.chunk_id != chunk.canonical_reference
    assert chunk.canonical_reference == "[Artículo 6]"
    assert chunk.paragraph_number == "1"


@pytest.mark.parametrize(
    "changes",
    [
        {"chunk_id": " "},
        {"text": " "},
        {"canonical_reference": ""},
        {"chunk_index": -1},
    ],
)
def test_invalid_regulation_chunks_are_rejected(changes: dict[str, object]) -> None:
    values: dict[str, object] = {
        "chunk_id": "chunk-1",
        "source_id": "source-1",
        "unit_type": "articulo",
        "unit_number": "1",
        "text": "Texto.",
        "canonical_reference": "[Artículo 1]",
        "content_hash": "hash",
    }
    values.update(changes)

    with pytest.raises(ValueError):
        RegulationChunk(**values)  # type: ignore[arg-type]


def test_source_evidence_and_answer_are_immutable_domain_values() -> None:
    source = RegulationSource(
        source_id="source-1",
        celex_id="32024R1689",
        source_url="https://eur-lex.europa.eu/",
        language="es",
        source_hash="hash",
        document_title="Reglamento",
    )
    evidence = Evidence(reference="[Artículo 1]", text="Texto exacto.", chunk_id="chunk-1")
    answer = Answer(answer="Respuesta.", references=(evidence.reference,), evidence=(evidence,))

    assert source.language == "es"
    assert answer.evidence[0].text == "Texto exacto."
    assert "no constituye asesoramiento jurídico" in answer.disclaimer