"""Local sentence-transformer embeddings and persistent Chroma storage."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import chromadb

from consulta_ai_act.models import RegulationChunk, RetrievedChunk


class TextEmbedder(Protocol):
    """Minimal embedding interface used for dependency injection and tests."""

    model_name: str

    def encode(
        self,
        texts: Sequence[str],
        *,
        input_type: str = "passage",
    ) -> Sequence[Sequence[float]]:
        """Encode texts into a consistent vector space."""
        ...


class SentenceTransformerEmbedder:
    """Generate local multilingual embeddings using Sentence Transformers."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, device="cpu")
        self.max_seq_length = self._model.max_seq_length
        self.requires_task_prefixes = "e5" in model_name.lower()

    def encode(
        self,
        texts: Sequence[str],
        *,
        input_type: str = "passage",
    ) -> Sequence[Sequence[float]]:
        if input_type not in {"passage", "query"}:
            raise ValueError("input_type must be 'passage' or 'query'")
        prepared_texts = [prepare_embedding_text(text, input_type, self.model_name) for text in texts]
        vectors = self._model.encode(
            prepared_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist() if hasattr(vectors, "tolist") else vectors



def prepare_embedding_text(text: str, input_type: str, model_name: str) -> str:
    """Apply E5 task prefixes once, leaving other embedding models unchanged."""
    if input_type not in {"passage", "query"}:
        raise ValueError("input_type must be 'passage' or 'query'")
    if "e5" not in model_name.lower():
        return text
    clean_text = text
    for prefix in ("query: ", "passage: "):
        if clean_text.startswith(prefix):
            clean_text = clean_text[len(prefix) :]
    return f"{input_type}: {clean_text}"


class ChromaVectorStore:
    """Persistent, idempotent vector storage for regulation chunks."""

    def __init__(
        self,
        path: str | Path,
        embedder: TextEmbedder,
        *,
        collection_name: str = "ai_act_es",
        reset: bool = False,
    ) -> None:
        self.embedder = embedder
        self.client = chromadb.PersistentClient(path=str(path))
        if reset:
            try:
                self.client.delete_collection(collection_name)
            except Exception as exc:
                if "does not exist" not in str(exc).lower():
                    raise
        try:
            existing_collection = self.client.get_collection(collection_name)
        except Exception as exc:
            if not isinstance(exc, chromadb.errors.NotFoundError):
                raise
            existing_collection = None

        if existing_collection is not None:
            recorded_model = (existing_collection.metadata or {}).get("embedding_model")
            if recorded_model != embedder.model_name:
                if existing_collection.count() > 0:
                    raise ValueError(
                        "Existing Chroma collection uses a different embedding model; "
                        "rebuild the index before querying it"
                    )
                self.client.delete_collection(collection_name)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "embedding_model": embedder.model_name},
        )

    def upsert(self, chunks: Sequence[RegulationChunk], *, batch_size: int = 64) -> int:
        """Insert or replace chunks by stable ID; repeated ingestion does not duplicate rows."""
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        for start in range(0, len(chunks), batch_size):
            batch = list(chunks[start : start + batch_size])
            vectors = self.embedder.encode([chunk.text for chunk in batch], input_type="passage")
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in batch],
                embeddings=[list(vector) for vector in vectors],
                documents=[chunk.text for chunk in batch],
                metadatas=[_chunk_metadata(chunk) for chunk in batch],
            )
        return len(chunks)

    def query(self, text: str, *, k: int = 5) -> list[RetrievedChunk]:
        """Return up to k nearest passages with cosine similarity and typed metadata."""
        if not text.strip():
            raise ValueError("query text must not be empty")
        if k < 1:
            raise ValueError("k must be positive")
        if self.collection.count() == 0:
            return []
        vector = list(self.embedder.encode([text], input_type="query")[0])
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=min(k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        retrieved: list[RetrievedChunk] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            chunk = _chunk_from_storage(chunk_id, document, metadata)
            similarity = min(1.0, max(0.0, 1.0 - float(distance)))
            retrieved.append(RetrievedChunk(chunk=chunk, score=similarity))
        return retrieved

    @property
    def count(self) -> int:
        """Number of unique chunks in the persistent collection."""
        return self.collection.count()


def _chunk_metadata(chunk: RegulationChunk) -> dict[str, str | int]:
    metadata: dict[str, str | int] = {
        "source_id": chunk.source_id,
        "unit_type": chunk.unit_type,
        "unit_number": chunk.unit_number,
        "canonical_reference": chunk.canonical_reference,
        "content_hash": chunk.content_hash,
        "chunk_index": chunk.chunk_index,
    }
    if chunk.unit_title is not None:
        metadata["unit_title"] = chunk.unit_title
    if chunk.paragraph_number is not None:
        metadata["paragraph_number"] = chunk.paragraph_number
    if chunk.locator is not None:
        metadata["locator"] = chunk.locator
    return metadata


def _chunk_from_storage(
    chunk_id: str,
    text: str,
    metadata: dict[str, str | int],
) -> RegulationChunk:
    return RegulationChunk(
        chunk_id=chunk_id,
        source_id=str(metadata["source_id"]),
        unit_type=str(metadata["unit_type"]),  # type: ignore[arg-type]
        unit_number=str(metadata["unit_number"]),
        text=text,
        canonical_reference=str(metadata["canonical_reference"]),
        content_hash=str(metadata["content_hash"]),
        unit_title=str(metadata["unit_title"]) if metadata.get("unit_title") is not None else None,
        paragraph_number=(
            str(metadata["paragraph_number"])
            if metadata.get("paragraph_number") is not None
            else None
        ),
        chunk_index=int(metadata["chunk_index"]),
        locator=str(metadata["locator"]) if metadata.get("locator") is not None else None,
    )
