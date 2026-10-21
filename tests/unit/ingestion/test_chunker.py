"""Tests for structure-preserving legal document chunking."""

from pathlib import Path

from consulta_ai_act.ingestion.chunker import chunk_regulation_html, chunk_to_json_dict

FIXTURE = Path(__file__).parents[2] / "fixtures" / "regulation_sample.html"
SOURCE_URL = "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689"


def test_chunker_splits_long_articles_at_numbered_paragraphs() -> None:
    _, chunks = chunk_regulation_html(
        FIXTURE.read_bytes(),
        source_url=SOURCE_URL,
        max_chunk_characters=180,
    )

    articles = [chunk for chunk in chunks if chunk.unit_type == "articulo"]
    article_one = [chunk for chunk in articles if chunk.unit_number == "1"]
    article_two = [chunk for chunk in articles if chunk.unit_number == "2"]

    assert len(article_one) == 1
    assert len(article_two) >= 2
    assert {chunk.paragraph_number for chunk in article_two} == {"1", "2"}
    assert all(chunk.canonical_reference == "[Artículo 2]" for chunk in article_two)
    assert all(chunk.chunk_id for chunk in chunks)
    assert all(chunk.content_hash for chunk in chunks)


def test_short_article_remains_one_chunk_with_title() -> None:
    _, chunks = chunk_regulation_html(FIXTURE.read_bytes(), source_url=SOURCE_URL)

    article_one = next(
        chunk for chunk in chunks if chunk.unit_type == "articulo" and chunk.unit_number == "1"
    )

    assert article_one.unit_title == "Objeto"
    assert article_one.paragraph_number is None
    assert "1. El Reglamento mejora el mercado interior." in article_one.text
    assert "2. Establece reglas comunes" in article_one.text


def test_debug_record_preserves_text_and_metadata() -> None:
    _, chunks = chunk_regulation_html(FIXTURE.read_bytes(), source_url=SOURCE_URL)
    record = chunk_to_json_dict(chunks[0])

    assert record["text"] == chunks[0].text
    assert record["reference"] == chunks[0].canonical_reference
    assert record["type"] == chunks[0].unit_type


def test_long_recital_splits_by_sentences_and_keeps_reference() -> None:
    fixture = FIXTURE.read_text(encoding="utf-8")
    expanded = fixture.replace(
        "Tercera oración que permite comprobar la división por oraciones sin perder la referencia al considerando.",
        "Tercera oración que permite comprobar la división por oraciones sin perder la referencia al considerando. "
        + "Esta oración adicional amplía el considerando con explicación normativa verificable. " * 12,
    )

    _, chunks = chunk_regulation_html(
        expanded,
        source_url=SOURCE_URL,
        max_chunk_characters=180,
    )
    recital_chunks = [
        chunk for chunk in chunks if chunk.unit_type == "considerando" and chunk.unit_number == "2"
    ]

    assert len(recital_chunks) > 1
    assert all(len(chunk.text) <= 180 for chunk in recital_chunks)
    assert all(chunk.canonical_reference == "[Considerando 2]" for chunk in recital_chunks)
    assert all(chunk.locator and "párrafo 1" in chunk.locator for chunk in recital_chunks)
    assert any("frase" in chunk.locator for chunk in recital_chunks if chunk.locator)


def test_article_three_splits_numbered_definitions_with_locator() -> None:
    _, chunks = chunk_regulation_html(
        FIXTURE.read_bytes(),
        source_url=SOURCE_URL,
        max_chunk_characters=120,
    )
    article_three = [
        chunk for chunk in chunks if chunk.unit_type == "articulo" and chunk.unit_number == "3"
    ]

    assert len(article_three) >= 2
    assert all(chunk.canonical_reference == "[Artículo 3]" for chunk in article_three)
    assert any(chunk.locator and "definición 1" in chunk.locator for chunk in article_three)


def test_annex_splits_by_sections_points_and_letters() -> None:
    _, chunks = chunk_regulation_html(
        FIXTURE.read_bytes(),
        source_url=SOURCE_URL,
        max_chunk_characters=40,
    )
    annex_two = [chunk for chunk in chunks if chunk.unit_type == "anexo" and chunk.unit_number == "II"]

    assert any(chunk.locator and "Sección A" in chunk.locator for chunk in annex_two)
    assert any(chunk.locator and "punto 1" in chunk.locator for chunk in annex_two)
    assert any(chunk.locator and "letra a)" in chunk.locator for chunk in annex_two)
    assert all(chunk.canonical_reference == "[Anexo II]" for chunk in annex_two)
    assert all(len(chunk.text) <= 40 for chunk in annex_two)
    assert all(chunk.locator for chunk in annex_two)


def test_oversized_sentence_is_split_on_word_boundaries() -> None:
    _, chunks = chunk_regulation_html(
        FIXTURE.read_bytes(),
        source_url=SOURCE_URL,
        max_chunk_characters=80,
    )
    recital_chunks = [
        chunk for chunk in chunks if chunk.unit_type == "considerando" and chunk.unit_number == "2"
    ]

    assert all(len(chunk.text) <= 80 for chunk in recital_chunks)
    assert all(chunk.text.strip() == chunk.text for chunk in recital_chunks)
