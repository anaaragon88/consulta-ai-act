"""Validated application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration with safe defaults for local development."""

    anthropic_api_key: str
    anthropic_model: str
    embedding_model: str
    retrieval_k: int
    retrieval_max_k: int
    retrieval_min_similarity: float
    max_question_length: int
    chroma_path: Path
    regulation_path: Path
    evaluation_dataset_path: Path
    evaluation_results_path: Path
    log_level: str

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> Settings:
        """Load and validate settings, without requiring an API key for offline tasks."""
        if load_dotenv_file:
            load_dotenv()

        settings = cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929").strip(),
            embedding_model=os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ).strip(),
            retrieval_k=_read_int("RETRIEVAL_K", 5),
            retrieval_max_k=_read_int("RETRIEVAL_MAX_K", 20),
            retrieval_min_similarity=_read_float("RETRIEVAL_MIN_SIMILARITY", 0.0),
            max_question_length=_read_int("MAX_QUESTION_LENGTH", 1000),
            chroma_path=Path(os.getenv("CHROMA_PATH", "chroma_db")),
            regulation_path=Path(os.getenv("REGULATION_PATH", "data/raw/regulation_es.html")),
            evaluation_dataset_path=Path(
                os.getenv("EVALUATION_DATASET_PATH", "data/eval/questions.jsonl")
            ),
            evaluation_results_path=Path(os.getenv("EVALUATION_RESULTS_PATH", "evals/results")),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Reject invalid settings before any service or model is initialized."""
        if not self.anthropic_model:
            raise ValueError("ANTHROPIC_MODEL must not be empty")
        if not self.embedding_model:
            raise ValueError("EMBEDDING_MODEL must not be empty")
        if self.retrieval_max_k < 1:
            raise ValueError("RETRIEVAL_MAX_K must be at least 1")
        if not 1 <= self.retrieval_k <= self.retrieval_max_k:
            raise ValueError("RETRIEVAL_K must be between 1 and RETRIEVAL_MAX_K")
        if self.max_question_length < 1:
            raise ValueError("MAX_QUESTION_LENGTH must be at least 1")
        if not 0.0 <= self.retrieval_min_similarity <= 1.0:
            raise ValueError("RETRIEVAL_MIN_SIMILARITY must be between 0 and 1")
        if self.log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("LOG_LEVEL must be a standard logging level")


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _read_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def require_anthropic_api_key(settings: Settings) -> str:
    """Return the API key for online generation or fail without exposing its value."""
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for answer generation")
    return settings.anthropic_api_key