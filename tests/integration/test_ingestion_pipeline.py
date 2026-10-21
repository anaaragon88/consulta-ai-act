"""Tests for the offline ingestion orchestration."""

import json
from collections.abc import Sequence
from pathlib import Path

from scripts.ingest_regulation import ingest_regulation

FIXTURE = Path(__file__).parents[1] / "fixtures" / "regulation_sample.html"


class DeterministicEmbedder:
    model_name = "test-pipeline-embedding-v1"

    def encode(
        self, texts: Sequence[str], *, input_type: str = "passage"
    ) -> Sequence[Sequence[float]]:
        return [[1.0, float(len(text) + 1)] for text in texts]


def test_pipeline_writes_all_chunks_and_indexes_them(tmp_path: Path) -> None:
    debug_path = tmp_path / "data" / "debug" / "chunks.jsonl"

    chunks, summary = ingest_regulation(
        source_path=FIXTURE,
        chroma_path=tmp_path / "chroma",
        debug_output_path=debug_path,
        embedder=DeterministicEmbedder(),
        max_chunk_characters=180,
    )

    rows = [json.loads(line) for line in debug_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len(chunks)
    assert summary["total_chunks"] == len(chunks)
    assert summary["collection_count"] == len(chunks)
    assert summary["chunks_by_type"]["considerando"] >= 2
    assert summary["chunks_by_type"]["articulo"] >= 4
    assert summary["chunks_by_type"]["anexo"] >= 2
    assert summary["chunk_length_characters"]["minimum"] > 0
    assert summary["chunk_length_characters"]["maximum"] <= 180
    assert summary["chunk_length_characters"]["maximum"] >= summary["chunk_length_characters"]["minimum"]
    assert {row["reference"] for row in rows} >= {"[Considerando 1]", "[Artículo 2]", "[Anexo I]"}
    assert any(row["locator"] for row in rows)
