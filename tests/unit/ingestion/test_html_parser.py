"""Tests for parsing EUR-Lex regulation structure and provenance."""

import hashlib
from pathlib import Path

import pytest

from consulta_ai_act.errors import SourceIngestionError
from consulta_ai_act.ingestion.html_parser import parse_regulation_file, parse_regulation_html

FIXTURE = Path(__file__).parents[2] / "fixtures" / "regulation_sample.html"


def test_parser_extracts_each_legal_unit_and_source_hash() -> None:
    raw = FIXTURE.read_bytes()

    source, chunks = parse_regulation_html(raw)

    assert source.celex_id == "32024R1689"
    assert source.language == "es"
    assert source.source_hash == hashlib.sha256(raw).hexdigest()
    assert source.source_id.endswith(source.source_hash[:16])
    assert {chunk.unit_type for chunk in chunks} == {"considerando", "articulo", "anexo"}
    assert any(chunk.canonical_reference == "[Artículo 1]" for chunk in chunks)
    assert any(chunk.canonical_reference == "[Anexo I]" for chunk in chunks)


def test_parser_file_reads_local_source(tmp_path: Path) -> None:
    source_path = tmp_path / "regulation.html"
    source_path.write_bytes(FIXTURE.read_bytes())

    source, chunks = parse_regulation_file(source_path)

    assert source.source_hash == hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert chunks


def test_parser_fails_closed_when_required_sections_are_missing() -> None:
    incomplete_html = "<html><head><title>Incomplete</title></head><body><div id='rct_1'>text</div></body></html>"

    with pytest.raises(SourceIngestionError, match="missing required sections"):
        parse_regulation_html(incomplete_html)


def test_parser_rejects_missing_document_title() -> None:
    with pytest.raises(SourceIngestionError, match="no title"):
        parse_regulation_html("<html><body></body></html>")
