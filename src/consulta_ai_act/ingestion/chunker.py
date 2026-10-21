"""Structure-aware chunking that preserves legal unit references."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from consulta_ai_act.errors import SourceIngestionError
from consulta_ai_act.models import RegulationChunk, RegulationSource
from consulta_ai_act.ingestion.html_parser import (
    _ARTICLE_ID,
    _PARAGRAPH_ID,
    _make_chunk,
    parse_regulation_html,
)

DEFAULT_LONG_ARTICLE_CHARS = 4_000
_PARAGRAPH_NUMBER = re.compile(r"^\s*(\d+)\.")


def chunk_regulation_html(
    html: str | bytes,
    *,
    source_url: str,
    max_article_chars: int = DEFAULT_LONG_ARTICLE_CHARS,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Keep each recital and annex intact; split long articles at numbered paragraphs."""
    if max_article_chars < 1:
        raise ValueError("max_article_chars must be positive")

    raw = html.encode("utf-8") if isinstance(html, str) else html
    source, parsed_chunks = parse_regulation_html(raw, source_url=source_url)
    soup = BeautifulSoup(raw, "html.parser")
    chunks: list[RegulationChunk] = []

    for chunk in parsed_chunks:
        if chunk.unit_type != "articulo" or len(chunk.text) <= max_article_chars:
            chunks.append(chunk)
            continue

        article = soup.find(id=f"art_{chunk.unit_number}")
        if not isinstance(article, Tag):
            raise SourceIngestionError(
                f"Official article {chunk.unit_number} disappeared during chunking"
            )
        paragraph_blocks = [
            node
            for node in article.find_all(id=_PARAGRAPH_ID)
            if isinstance(node, Tag) and node.find_parent(id=_ARTICLE_ID) is article
        ]
        if not paragraph_blocks:
            chunks.append(chunk)
            continue

        for index, block in enumerate(paragraph_blocks):
            paragraph_text = block.get_text(" ", strip=True)
            if not paragraph_text:
                continue
            number_match = _PARAGRAPH_NUMBER.match(paragraph_text)
            paragraph_number = number_match.group(1) if number_match else None
            chunks.append(
                _make_chunk(
                    source=source,
                    unit_type="articulo",
                    number=chunk.unit_number,
                    title=chunk.unit_title,
                    text=paragraph_text,
                    paragraph_number=paragraph_number,
                    chunk_index=index,
                )
            )

    return source, chunks


def chunk_regulation_file(
    path: str | Path,
    *,
    source_url: str,
    max_article_chars: int = DEFAULT_LONG_ARTICLE_CHARS,
) -> tuple[RegulationSource, list[RegulationChunk]]:
    """Chunk a local source file without network access."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise SourceIngestionError("Regulation source file could not be read") from exc
    return chunk_regulation_html(
        raw,
        source_url=source_url,
        max_article_chars=max_article_chars,
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
