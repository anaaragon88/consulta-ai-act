"""Tests for environment-backed settings validation."""

import pytest

from consulta_ai_act.config import Settings


def test_settings_use_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = Settings.from_env(load_dotenv_file=False)

    assert settings.retrieval_k == 5
    assert settings.retrieval_max_k == 20
    assert settings.max_question_length == 1000
    assert settings.anthropic_api_key == ""
    assert settings.embedding_model.endswith("paraphrase-multilingual-MiniLM-L12-v2")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RETRIEVAL_K", "0"),
        ("RETRIEVAL_K", "21"),
        ("RETRIEVAL_K", "not-an-integer"),
        ("RETRIEVAL_MAX_K", "0"),
        ("MAX_QUESTION_LENGTH", "0"),
        ("RETRIEVAL_MIN_SIMILARITY", "1.1"),
        ("RETRIEVAL_MIN_SIMILARITY", "not-a-number"),
        ("LOG_LEVEL", "TRACE"),
    ],
)
def test_invalid_settings_are_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        Settings.from_env(load_dotenv_file=False)


def test_retrieval_k_can_be_configured_within_maximum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RETRIEVAL_K", "10")
    monkeypatch.setenv("RETRIEVAL_MAX_K", "12")

    settings = Settings.from_env(load_dotenv_file=False)

    assert settings.retrieval_k == 10