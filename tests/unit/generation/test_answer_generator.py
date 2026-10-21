"""Tests for evidence-only Spanish responses with a mocked Anthropic SDK."""

from types import SimpleNamespace

from consulta_ai_act.config import Settings
from consulta_ai_act.models import RegulationChunk, RetrievedChunk
from consulta_ai_act.generation.answer_generator import AnswerGenerator, ABSTENTION_TEXT


class FakeMessages:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.kwargs = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.response_text)])


class FakeAnthropicClient:
    def __init__(self, response_text: str) -> None:
        self.messages = FakeMessages(response_text)


def _evidence() -> list[RetrievedChunk]:
    chunk = RegulationChunk(
        chunk_id="chunk-1",
        source_id="source-1",
        unit_type="articulo",
        unit_number="1",
        text="El presente Reglamento establece normas armonizadas.",
        canonical_reference="[Artículo 1]",
        content_hash="hash-1",
    )
    return [RetrievedChunk(chunk=chunk, score=0.91)]


def test_generator_sends_delimited_context_and_returns_spanish_answer() -> None:
    client = FakeAnthropicClient("El Reglamento establece normas armonizadas [Artículo 1].")
    settings = Settings.from_env(load_dotenv_file=False)
    generator = AnswerGenerator(settings, client=client)

    answer = generator.generate("¿Qué establece el Reglamento?", _evidence())

    assert answer == "El Reglamento establece normas armonizadas [Artículo 1]."
    assert "<retrieved_context>" in str(client.messages.kwargs["messages"])
    assert "</retrieved_context>" in str(client.messages.kwargs["messages"])
    assert "<untrusted_regulation_data>" in str(client.messages.kwargs["messages"])
    assert "</untrusted_regulation_data>" in str(client.messages.kwargs["messages"])
    assert "usando exclusivamente el contexto recuperado" in str(
        client.messages.kwargs["system"]
    ).lower()
    assert client.messages.kwargs["model"] == settings.anthropic_model


def test_generator_uses_fixed_abstention_for_empty_context() -> None:
    client = FakeAnthropicClient("This must not be called")
    generator = AnswerGenerator(Settings.from_env(load_dotenv_file=False), client=client)

    answer = generator.generate("pregunta sin evidencia", [])

    assert answer == ABSTENTION_TEXT
    assert client.messages.kwargs is None