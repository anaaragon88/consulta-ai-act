"""Tests for E5's query/passage embedding task prefixes."""

from collections.abc import Sequence
from typing import Any

from consulta_ai_act.retrieval.vector_store import (
    SentenceTransformerEmbedder,
    prepare_embedding_text,
)


def test_e5_prefixes_are_selected_by_task_and_added_once() -> None:
    model = "intfloat/multilingual-e5-small"

    assert prepare_embedding_text("Texto legal", "passage", model) == "passage: Texto legal"
    assert prepare_embedding_text("consulta", "query", model) == "query: consulta"
    assert prepare_embedding_text("passage: Texto legal", "passage", model) == "passage: Texto legal"
    assert prepare_embedding_text("query: consulta", "query", model) == "query: consulta"


def test_non_e5_model_does_not_receive_e5_prefix() -> None:
    assert (
        prepare_embedding_text("Texto legal", "passage", "sentence-transformers/other-model")
        == "Texto legal"
    )


def test_sentence_transformer_adapter_encodes_prefixed_text(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    class FakeModel:
        max_seq_length = 512

        def encode(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
            calls.append(texts)
            return [[1.0, 0.0] for _ in texts]

    class FakeSentenceTransformer:
        def __init__(self, model_name: str, device: str) -> None:
            assert model_name == "intfloat/multilingual-e5-small"
            assert device == "cpu"
            self.model = FakeModel()
            self.max_seq_length = self.model.max_seq_length

        def encode(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
            return self.model.encode(texts, **kwargs)

    import sentence_transformers

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", FakeSentenceTransformer)
    embedder = SentenceTransformerEmbedder("intfloat/multilingual-e5-small")

    embedder.encode(["Texto de reglamento"], input_type="passage")
    embedder.encode(["¿Qué establece?"], input_type="query")

    assert embedder.max_seq_length == 512
    assert calls == [["passage: Texto de reglamento"], ["query: ¿Qué establece?"]]
