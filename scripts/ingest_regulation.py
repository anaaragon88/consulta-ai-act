"""Ingest the local official regulation into debug JSONL and persistent Chroma."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from consulta_ai_act.config import Settings
from consulta_ai_act.ingestion.chunker import chunk_regulation_file, chunk_to_json_dict
from consulta_ai_act.ingestion.html_parser import PUBLICATIONS_SOURCE_URL
from consulta_ai_act.models import RegulationChunk
from consulta_ai_act.retrieval.vector_store import ChromaVectorStore, SentenceTransformerEmbedder, TextEmbedder


def write_chunks_jsonl(chunks: list[RegulationChunk], output_path: str | Path) -> None:
    """Write every chunk as one UTF-8 JSON record per line, atomically."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as output:
        for chunk in chunks:
            output.write(json.dumps(chunk_to_json_dict(chunk), ensure_ascii=False) + "\n")
    temporary_path.replace(path)


def summarize_chunks(chunks: list[RegulationChunk]) -> dict[str, Any]:
    """Return total chunks by legal type and character-length summary."""
    counts = Counter(chunk.unit_type for chunk in chunks)
    lengths = [len(chunk.text) for chunk in chunks]
    return {
        "total_chunks": len(chunks),
        "chunks_by_type": {
            "considerando": counts.get("considerando", 0),
            "articulo": counts.get("articulo", 0),
            "anexo": counts.get("anexo", 0),
        },
        "chunk_length_characters": {
            "minimum": min(lengths) if lengths else 0,
            "mean": round(statistics.fmean(lengths), 2) if lengths else 0,
            "maximum": max(lengths) if lengths else 0,
        },
    }


def ingest_regulation(
    *,
    source_path: str | Path,
    chroma_path: str | Path,
    debug_output_path: str | Path,
    embedder: TextEmbedder | None = None,
    max_article_chars: int = 4_000,
    reset_index: bool = False,
) -> tuple[list[RegulationChunk], dict[str, Any]]:
    """Parse, chunk, persist debug records, and upsert the regulation index."""
    _, chunks = chunk_regulation_file(
        source_path,
        source_url=PUBLICATIONS_SOURCE_URL,
        max_article_chars=max_article_chars,
    )
    write_chunks_jsonl(chunks, debug_output_path)
    active_embedder = embedder or SentenceTransformerEmbedder(
        Settings.from_env().embedding_model
    )
    vector_store = ChromaVectorStore(chroma_path, active_embedder, reset=reset_index)
    vector_store.upsert(chunks)
    summary = summarize_chunks(chunks)
    summary.update(
        {
            "source_path": str(Path(source_path)),
            "debug_output_path": str(Path(debug_output_path)),
            "chroma_path": str(Path(chroma_path)),
            "collection_count": vector_store.count,
            "embedding_model": active_embedder.model_name,
        }
    )
    return chunks, summary


def main() -> None:
    """Run local ingestion from configured paths."""
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=settings.regulation_path)
    parser.add_argument("--chroma-path", type=Path, default=settings.chroma_path)
    parser.add_argument("--debug-output", type=Path, default=Path("data/debug/chunks.jsonl"))
    parser.add_argument("--max-article-chars", type=int, default=4_000)
    parser.add_argument("--reset-index", action="store_true")
    args = parser.parse_args()

    _, summary = ingest_regulation(
        source_path=args.source,
        chroma_path=args.chroma_path,
        debug_output_path=args.debug_output,
        max_article_chars=args.max_article_chars,
        reset_index=args.reset_index,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
