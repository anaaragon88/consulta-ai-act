"""Tests for configurable top-k retrieval and returned metadata."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from consulta_ai_act.config import Settings
from consulta_ai_act.ingestion.chunker import chunk_regulation_html
from consulta_ai_act.retrieval.retriever import RegulationRetriever
from consulta_ai_act.retrieval.vector_store import ChromaVectorStore

FIXTURE = Path(__file__).parents[2] / "fixtures" / "regulation_sample.html"


class RecordingEmbedder:
    model_name = "retriever-test-model"

    def encode(
        self, texts: Sequence[str], *, input_type: str = "passage"
    ) -> Sequence[Sequence[float]]:
        return [[1.0, float(len(text) % 10 + 1)] for text in texts]


def test_retriever_uses_five_by_default_and_keeps_citation_metadata(tmp_path: Path) -> None:
    source_url = "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689"
    _, chunks = chunk_regulation_html(FIXTURE.read_bytes(), source_url=source_url)
    store = ChromaVectorStore(tmp_path / "chroma", RecordingEmbedder())
    store.upsert(chunks)
    settings = Settings.from_env(load_dotenv_file=False)
    retriever = RegulationRetriever(store, settings)

    result = retriever.retrieve("¿Qué regula el artículo 1?")

    assert len(result) == 5
    assert all(item.chunk.canonical_reference for item in result)
    assert all(0.0 <= item.score <= 1.0 for item in result)


def test_retriever_honors_configured_k(tmp_path: Path) -> None:
    source_url = "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689"
    _, chunks = chunk_regulation_html(FIXTURE.read_bytes(), source_url=source_url)
    store = ChromaVectorStore(tmp_path / "chroma", RecordingEmbedder())
    store.upsert(chunks)
    settings = Settings.from_env(load_dotenv_file=False)
    retriever = RegulationRetriever(store, settings)

    assert len(retriever.retrieve("pregunta legal", k=2)) == 2


@pytest.mark.parametrize("k", [0, 21])
def test_retriever_rejects_invalid_k(k: int, tmp_path: Path) -> None:
    store = ChromaVectorStore(tmp_path / "chroma", RecordingEmbedder())
    retriever = RegulationRetriever(store, Settings.from_env(load_dotenv_file=False))

    with pytest.raises(ValueError):
        retriever.retrieve("pregunta legal", k=k)