"""Parse the official EUR-Lex XHTML representation of the AI Act."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from consulta_ai_act.errors import SourceIngestionError
from consulta_ai_act.models import RegulationChunk, RegulationSource, UnitType

CELEX_ID = "32024R1689"
OFFICIAL_SOURCE_URL = "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689"
PUBLICATIONS_SOURCE_URL = (
    "https://publications.europa.eu/resource/oj/L_202401689.SPA.xhtml."
    "L_202401689ES.html"
)

_ARTICLE_ID = re.compile(r"^art_(\d+)$")
_RECITAL_ID = re.compile(r"^rct_(\d+)$")
_ANNEX_ID = re.compile(r"^anx_([IVXLCDM]+)$", re.IGNORECASE)
_PARAGRAPH_ID = re.compile(r"^\d{3}\.\d{3}$")


def parse_regulation_html(
    html: str | bytes,
    *,
    source_url: str = OFFICIAL_SOURCE_URL,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Parse recitals, articles, and annexes or fail rather than index partial text."""
    raw = html.encode("utf-8") if isinstance(html, str) else html
    source_hash = hashlib.sha256(raw).hexdigest()
    soup = BeautifulSoup(raw, "html.parser")
    title = _document_title(soup)

    source = RegulationSource(
        source_id=f"{CELEX_ID}:{source_hash[:16]}",
        celex_id=CELEX_ID,
        source_url=source_url,
        language="es",
        source_hash=source_hash,
        document_title=title,
    )

    chunks: list[RegulationChunk] = []
    chunks.extend(_parse_units(soup, source, "considerando", _RECITAL_ID))
    chunks.extend(_parse_units(soup, source, "articulo", _ARTICLE_ID))
    chunks.extend(_parse_units(soup, source, "anexo", _ANNEX_ID))

    types_found = {chunk.unit_type for chunk in chunks}
    missing = {"considerando", "articulo", "anexo"} - types_found
    if missing:
        missing_names = ", ".join(sorted(missing))
        raise SourceIngestionError(f"Official document is missing required sections: {missing_names}")
    return source, chunks


def parse_regulation_file(
    path: str | Path,
    *,
    source_url: str = OFFICIAL_SOURCE_URL,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Read a local official document and parse it without making network requests."""
    source_path = Path(path)
    try:
        raw = source_path.read_bytes()
    except OSError as exc:
        raise SourceIngestionError("Regulation source file could not be read") from exc
    return parse_regulation_html(raw, source_url=source_url)


def _document_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find("title")
    if title_tag is None:
        raise SourceIngestionError("Official document has no title")
    title = title_tag.get_text(" ", strip=True)
    if not title:
        raise SourceIngestionError("Official document has an empty title")
    return title


def _parse_units(
    soup: BeautifulSoup,
    source: RegulationSource,
    unit_type: UnitType,
    identifier_pattern: re.Pattern[str],
) -> list[RegulationChunk]:
    chunks: list[RegulationChunk] = []
    for unit in soup.find_all(id=identifier_pattern):
        if not isinstance(unit, Tag):
            continue
        match = identifier_pattern.fullmatch(str(unit.get("id", "")))
        if match is None:
            continue
        number = match.group(1)
        title = _unit_title(unit, unit_type)
        text = unit.get_text(" ", strip=True)
        if not text:
            raise SourceIngestionError(f"Official {unit_type} {number} has no text")
        chunks.append(
            _make_chunk(
                source=source,
                unit_type=unit_type,
                number=number,
                title=title,
                text=text,
                paragraph_number=None,
                chunk_index=0,
            )
        )
    return chunks


def _unit_title(unit: Tag, unit_type: UnitType) -> str | None:
    if unit_type == "articulo":
        title = unit.select_one(".eli-title .oj-sti-art")
        return title.get_text(" ", strip=True) if title else None
    if unit_type == "anexo":
        paragraphs = unit.select(".oj-doc-ti")
        if len(paragraphs) > 1:
            return paragraphs[1].get_text(" ", strip=True) or None
    return None


def _make_chunk(
    *,
    source: RegulationSource,
    unit_type: UnitType,
    number: str,
    title: str | None,
    text: str,
    paragraph_number: str | None,
    chunk_index: int,
    locator: str | None = None,
) -> RegulationChunk:
    reference_type = {
        "articulo": "Artículo",
        "considerando": "Considerando",
        "anexo": "Anexo",
    }[unit_type]
    canonical_reference = f"[{reference_type} {number}]"
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    identity = (
        f"{source.source_id}:{unit_type}:{number}:{paragraph_number or 'all'}:"
        f"{locator or ''}:{chunk_index}"
    )
    chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return RegulationChunk(
        chunk_id=chunk_id,
        source_id=source.source_id,
        unit_type=unit_type,
        unit_number=number,
        text=text,
        canonical_reference=canonical_reference,
        content_hash=content_hash,
        unit_title=title,
        paragraph_number=paragraph_number,
        chunk_index=chunk_index,
        locator=locator,
    )
