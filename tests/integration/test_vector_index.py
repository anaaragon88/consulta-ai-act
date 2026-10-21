"""Integration tests for Chroma persistence and stable chunk upserts."""

from collections.abc import Sequence
from pathlib import Path

from consulta_ai_act.ingestion.chunker import chunk_regulation_html
from consulta_ai_act.retrieval.vector_store import ChromaVectorStore

FIXTURE = Path(__file__).parents[1] / "fixtures" / "regulation_sample.html"
SOURCE_URL = "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689"


class DeterministicEmbedder:
    model_name = "test-deterministic-embedding-v1"

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        vectors = []
        for text in texts:
            vector = [float(len(text) % 97 + 1), float(text.lower().count("reglamento") + 1), 1.0]
            norm = sum(value * value for value in vector) ** 0.5
            vectors.append([value / norm for value in vector])
        return vectors


def test_chroma_upsert_is_idempotent_and_query_keeps_metadata(tmp_path: Path) -> None:
    _, chunks = chunk_regulation_html(FIXTURE.read_bytes(), source_url=SOURCE_URL)
    embedder = DeterministicEmbedder()
    store = ChromaVectorStore(tmp_path / "chroma", embedder)

    assert store.upsert(chunks) == len(chunks)
    assert store.count == len(chunks)
    assert store.upsert(chunks) == len(chunks)
    assert store.count == len(chunks)

    results = store.query("¿Qué establece el Reglamento?", k=5)

    assert len(results) == min(5, len(chunks))
    assert all(item.chunk.canonical_reference for item in results)
    assert all(0 <= item.score <= 1 for item in results)

    reopened = ChromaVectorStore(tmp_path / "chroma", embedder)
    assert reopened.count == len(chunks)


def test_store_refuses_to_reuse_collection_with_different_embedding_model(tmp_path: Path) -> None:
    ChromaVectorStore(tmp_path / "chroma", DeterministicEmbedder())

    class DifferentEmbedder(DeterministicEmbedder):
        model_name = "another-model"

    try:
        ChromaVectorStore(tmp_path / "chroma", DifferentEmbedder())
    except ValueError as error:
        assert "different embedding model" in str(error)
    else:
        raise AssertionError("A mismatched embedding model must not reuse an existing index")
