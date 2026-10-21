"""Structure-aware chunking that preserves legal unit references."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from consulta_ai_act.errors import SourceIngestionError
from consulta_ai_act.models import RegulationChunk, RegulationSource
from consulta_ai_act.ingestion.html_parser import (
    _ANNEX_ID,
    _ARTICLE_ID,
    _PARAGRAPH_ID,
    _RECITAL_ID,
    _make_chunk,
    parse_regulation_html,
)

DEFAULT_MAX_CHUNK_CHARACTERS = 1_500
_PARAGRAPH_NUMBER = re.compile(r"^\s*(\d+)\.")
_DEFINITION_NUMBER = re.compile(r"^\s*(\d+)\)\s*")
_LETTER_NUMBER = re.compile(r"^\s*([a-z])\)\s*", re.IGNORECASE)
_POINT_NUMBER = re.compile(r"^\s*(\d+)[.)]\s*")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?;])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡0-9])")
_CLAUSE_BOUNDARY = re.compile(r"(?<=[,;:])\s+")


def chunk_regulation_html(
    html: str | bytes,
    *,
    source_url: str,
    max_chunk_characters: int = DEFAULT_MAX_CHUNK_CHARACTERS,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Split long legal units by structure, then by sentence as a last resort."""
    if max_chunk_characters < 1:
        raise ValueError("max_chunk_characters must be positive")

    raw = html.encode("utf-8") if isinstance(html, str) else html
    source, parsed_chunks = parse_regulation_html(raw, source_url=source_url)
    soup = BeautifulSoup(raw, "html.parser")
    chunks: list[RegulationChunk] = []

    for chunk in parsed_chunks:
        if len(chunk.text) <= max_chunk_characters:
            chunks.append(chunk)
            continue
        unit = _find_unit(soup, chunk)
        if unit is None:
            raise SourceIngestionError(
                f"Official {chunk.unit_type} {chunk.unit_number} disappeared during chunking"
            )
        structural_units = _extract_structural_units(unit, chunk)
        if not structural_units:
            structural_units = [(chunk.text, None, None)]

        piece_index = 0
        for text, paragraph_number, locator in structural_units:
            pieces = (
                [(text, locator)]
                if len(text) <= max_chunk_characters
                else [
                    (sentence, _combine_locator(locator, f"frase {sentence_index + 1}"))
                    for sentence_index, sentence in enumerate(
                        _split_long_text(text, max_chunk_characters)
                    )
                ]
            )
            for piece, piece_locator in pieces:
                if not piece.strip():
                    continue
                chunks.append(
                    _make_chunk(
                        source=source,
                        unit_type=chunk.unit_type,
                        number=chunk.unit_number,
                        title=chunk.unit_title,
                        text=piece.strip(),
                        paragraph_number=paragraph_number,
                        chunk_index=piece_index,
                        locator=piece_locator,
                    )
                )
                piece_index += 1

    return source, chunks


def chunk_regulation_file(
    path: str | Path,
    *,
    source_url: str,
    max_chunk_characters: int = DEFAULT_MAX_CHUNK_CHARACTERS,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Chunk a local source file without network access."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise SourceIngestionError("Regulation source file could not be read") from exc
    return chunk_regulation_html(
        raw,
        source_url=source_url,
        max_chunk_characters=max_chunk_characters,
    )


def chunk_to_json_dict(chunk: RegulationChunk) -> dict[str, object]:
    """Serialize a chunk to a JSON-compatible record for inspection and persistence."""
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "type": chunk.unit_type,
        "number": chunk.unit_number,
        "title": chunk.unit_title,
        "paragraph_number": chunk.paragraph_number,
        "chunk_index": chunk.chunk_index,
        "locator": chunk.locator,
        "reference": chunk.canonical_reference,
        "text": chunk.text,
        "content_hash": chunk.content_hash,
    }


def chunk_collection_hash(chunks: list[RegulationChunk]) -> str:
    """Return a stable digest for the exact ordered chunk collection."""
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.chunk_id.encode("utf-8"))
        digest.update(chunk.content_hash.encode("utf-8"))
    return digest.hexdigest()


def _find_unit(soup: BeautifulSoup, chunk: RegulationChunk) -> Tag | None:
    identifiers = {
        "articulo": _ARTICLE_ID,
        "considerando": _RECITAL_ID,
        "anexo": _ANNEX_ID,
    }
    match = soup.find(id=identifiers[chunk.unit_type])
    if not isinstance(match, Tag):
        return None
    for unit in soup.find_all(id=identifiers[chunk.unit_type]):
        if not isinstance(unit, Tag):
            continue
        unit_match = identifiers[chunk.unit_type].fullmatch(str(unit.get("id", "")))
        if unit_match and unit_match.group(1) == chunk.unit_number:
            return unit
    return match


def _extract_structural_units(
    unit: Tag,
    chunk: RegulationChunk,
) -> list[tuple[str, str | None, str | None]]:
    if chunk.unit_type == "articulo":
        return _article_units(unit, chunk)
    if chunk.unit_type == "anexo":
        return _annex_units(unit)
    return _recital_units(unit, chunk)


def _recital_units(
    recital: Tag,
    chunk: RegulationChunk,
) -> list[tuple[str, str | None, str | None]]:
    paragraphs: list[str] = []
    for row in _leaf_table_rows(recital):
        cells = row.find_all(["td", "th"], recursive=False)
        text = cells[-1].get_text(" ", strip=True) if cells else row.get_text(" ", strip=True)
        if text and not re.fullmatch(r"\(\d+\)", text):
            paragraphs.append(text)
    if not paragraphs:
        paragraphs = [
            paragraph.get_text(" ", strip=True)
            for paragraph in recital.find_all("p", class_="oj-normal")
            if paragraph.get_text(" ", strip=True)
            and not re.fullmatch(r"\(\d+\)", paragraph.get_text(" ", strip=True))
        ]
    if not paragraphs:
        return [(chunk.text, None, "párrafo 1")]
    return [
        (text, None, f"párrafo {index}")
        for index, text in enumerate(paragraphs, start=1)
    ]


def _article_units(
    article: Tag,
    chunk: RegulationChunk,
) -> list[tuple[str, str | None, str | None]]:
    paragraph_blocks = [
        node
        for node in article.find_all(id=_PARAGRAPH_ID)
        if isinstance(node, Tag) and node.find_parent(id=_ARTICLE_ID) is article
    ]
    if paragraph_blocks:
        units: list[tuple[str, str | None, str | None]] = []
        for block in paragraph_blocks:
            text = block.get_text(" ", strip=True)
            number_match = _PARAGRAPH_NUMBER.match(text)
            paragraph_number = number_match.group(1) if number_match else None
            base_locator = f"apartado {paragraph_number}" if paragraph_number else None
            if len(text) > DEFAULT_MAX_CHUNK_CHARACTERS:
                rows = _leaf_table_rows(block)
                if rows:
                    for row in rows:
                        row_text = row.get_text(" ", strip=True)
                        locator = _combine_locator(base_locator, _list_locator(row_text))
                        units.append((row_text, paragraph_number, locator))
                    continue
            units.append((text, paragraph_number, base_locator))
        return units

    if chunk.unit_number == "3":
        definitions = _leaf_table_rows(article)
        if definitions:
            result = [
                (paragraph.get_text(" ", strip=True), None, "introducción")
                for paragraph in article.find_all("p", class_="oj-normal", recursive=False)
                if paragraph.get_text(" ", strip=True)
            ]
            for row in definitions:
                text = row.get_text(" ", strip=True)
                match = _DEFINITION_NUMBER.match(text)
                locator = f"definición {match.group(1)}" if match else _list_locator(text)
                result.append((text, None, locator))
            return result

    return _split_table_rows(article)


def _annex_units(annex: Tag) -> list[tuple[str, str | None, str | None]]:
    sections = annex.select(".oj-ti-grseq-1, .oj-ti-grseq-2, .oj-ti-grseq-3")
    if sections:
        units: list[tuple[str, str | None, str | None]] = []
        current_heading: str | None = None
        for child in annex.find_all(recursive=False):
            if not isinstance(child, Tag):
                continue
            classes = child.get("class", [])
            if any(str(css_class).startswith("oj-ti-grseq") for css_class in classes):
                current_heading = child.get_text(" ", strip=True)
                units.append((current_heading, None, f"sección {current_heading}"))
            elif child.name == "table":
                for row in _leaf_table_rows(child):
                    text = row.get_text(" ", strip=True)
                    if text:
                        units.append((text, None, _combine_locator(current_heading, _list_locator(text))))
            elif child.name in {"p", "div"} and child.get_text(" ", strip=True):
                text = child.get_text(" ", strip=True)
                if "oj-doc-ti" not in classes and not any(
                    str(css_class).startswith("oj-ti-grseq") for css_class in classes
                ):
                    units.append((text, None, _combine_locator(current_heading, _list_locator(text))))
        return units
    return _split_table_rows(annex)


def _split_table_rows(container: Tag) -> list[tuple[str, str | None, str | None]]:
    rows = _leaf_table_rows(container)
    return [
        (row.get_text(" ", strip=True), None, _list_locator(row.get_text(" ", strip=True)))
        for row in rows
        if row.get_text(" ", strip=True)
    ]


def _leaf_table_rows(container: Tag) -> list[Tag]:
    rows = [row for row in container.find_all("tr") if isinstance(row, Tag)]
    return [row for row in rows if not row.find("tr")]


def _list_locator(text: str) -> str | None:
    definition = _DEFINITION_NUMBER.match(text)
    if definition:
        return f"definición {definition.group(1)}"
    letter = _LETTER_NUMBER.match(text)
    if letter:
        return f"letra {letter.group(1).lower()})"
    point = _POINT_NUMBER.match(text)
    if point:
        return f"punto {point.group(1)}"
    return None


def _combine_locator(parent: str | None, child: str | None) -> str | None:
    if parent and child:
        return f"{parent}, {child}"
    return parent or child


def _split_long_text(text: str, max_characters: int) -> list[str]:
    sentences = [part.strip() for part in _SENTENCE_BOUNDARY.split(text.strip()) if part.strip()]
    if len(sentences) <= 1:
        sentences = [text.strip()]
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_characters:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_split_oversized_sentence(sentence, max_characters))
        elif current and len(current) + 1 + len(sentence) > max_characters:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    bounded: list[str] = []
    for piece in pieces:
        if len(piece) <= max_characters:
            bounded.append(piece)
        else:
            bounded.extend(_split_oversized_sentence(piece, max_characters))
    return bounded


def _split_oversized_sentence(sentence: str, max_characters: int) -> list[str]:
    clauses = [part.strip() for part in _CLAUSE_BOUNDARY.split(sentence) if part.strip()]
    if len(clauses) == 1:
        clauses = sentence.split()
        units: list[str] = []
        current = ""
        for word in clauses:
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > max_characters:
                units.append(current)
                current = word
            else:
                current = candidate
        if current:
            units.append(current)
        return units

    units = []
    current = ""
    for clause in clauses:
        candidate = f"{current}, {clause}".strip(", ")
        if current and len(candidate) > max_characters:
            units.append(current)
            current = clause
        else:
            current = candidate
    if current:
        units.append(current)
    return units
