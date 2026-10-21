"""Contract tests for a successful POST /ask response with mocked dependencies."""

from fastapi.testclient import TestClient

from consulta_ai_act.api.app import create_app
from consulta_ai_act.models import Answer, Evidence, RegulationChunk, RetrievedChunk


class FakeRetriever:
    def retrieve(self, question: str, *, k: int | None = None) -> list[RetrievedChunk]:
        chunk = RegulationChunk(
            chunk_id="chunk-1",
            source_id="source-1",
            unit_type="articulo",
            unit_number="1",
            text="El presente Reglamento establece normas armonizadas.",
            canonical_reference="[Artículo 1]",
            content_hash="hash-1",
        )
        return [RetrievedChunk(chunk=chunk, score=0.92)]


class FakeGenerator:
    def generate(self, question: str, evidence: list[RetrievedChunk]) -> str:
        return "El Reglamento establece normas armonizadas [Artículo 1]."


class FakeCitationValidator:
    def validate(self, answer: str, evidence: list[RetrievedChunk]) -> tuple[str, ...]:
        return ("[Artículo 1]",)


class FakeAnswerService:
    def ask(self, question: str, *, k: int | None = None) -> Answer:
        chunk = RegulationChunk(
            chunk_id="chunk-1",
            source_id="source-1",
            unit_type="articulo",
            unit_number="1",
            text="El presente Reglamento establece normas armonizadas.",
            canonical_reference="[Artículo 1]",
            content_hash="hash-1",
        )
        return Answer(
            answer="El Reglamento establece normas armonizadas [Artículo 1].",
            references=("[Artículo 1]",),
            evidence=(Evidence("[Artículo 1]", chunk.text, chunk.chunk_id),),
        )


def test_post_ask_returns_answer_references_evidence_and_disclaimer() -> None:
    app = create_app(answer_service=FakeAnswerService())

    with TestClient(app) as client:
        response = client.post("/ask", json={"question": "¿Qué establece el Reglamento?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].endswith("[Artículo 1].")
    assert payload["references"] == ["[Artículo 1]"]
    assert payload["evidence"] == [
        {
            "reference": "[Artículo 1]",
            "text": "El presente Reglamento establece normas armonizadas.",
        }
    ]
    assert "no constituye asesoramiento jurídico" in payload["disclaimer"]
    assert payload["abstained"] is False
