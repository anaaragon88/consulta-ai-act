"""Top-k retrieval wrapper with validated configuration and relevance scores."""

from __future__ import annotations

from consulta_ai_act.config import Settings
from consulta_ai_act.models import RetrievedChunk
from consulta_ai_act.retrieval.vector_store import ChromaVectorStore


class RegulationRetriever:
    """Retrieve ranked regulation passages with canonical citation metadata."""

    def __init__(self, vector_store: ChromaVectorStore, settings: Settings) -> None:
        self.vector_store = vector_store
        self.settings = settings

    def retrieve(self, question: str, *, k: int | None = None) -> list[RetrievedChunk]:
        if not question.strip():
            raise ValueError("Question must not be empty")
        requested_k = self.settings.retrieval_k if k is None else k
        if not 1 <= requested_k <= self.settings.retrieval_max_k:
            raise ValueError("k must be between 1 and RETRIEVAL_MAX_K")
        return self.vector_store.query(question, k=requested_k)
