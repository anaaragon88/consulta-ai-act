"""Pydantic request and response models for the public API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=1000)
    k: int | None = Field(default=None, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question must not be empty")
        if len(question) > 1000:
            raise ValueError("Question exceeds the 1000-character limit")
        return question


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    text: str


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    references: list[str]
    evidence: list[EvidenceResponse]
    disclaimer: str
    abstained: bool


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: str
    message: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    index_ready: bool
