"""HTTP endpoints for legal-regulation questions and service health."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from consulta_ai_act.api.schemas import (
    AskRequest,
    AskResponse,
    ErrorResponse,
    EvidenceResponse,
    HealthResponse,
)
from consulta_ai_act.errors import CitationValidationError, ConfigurationError
from consulta_ai_act.logging_config import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def ask(request: Request, payload: AskRequest) -> AskResponse:
    service = request.app.state.answer_service
    if service is None:
        try:
            service = request.app.state.service_factory()
            request.app.state.answer_service = service
        except (FileNotFoundError, ValueError, RuntimeError):
            logger.warning("answer service unavailable")
            raise HTTPException(
                status_code=503,
                detail={"error": "service_unavailable", "message": "El asistente no está disponible."},
            ) from None

    try:
        answer = service.ask(payload.question, k=payload.k)
    except CitationValidationError:
        logger.error("generated citation failed validation")
        raise HTTPException(
            status_code=502,
            detail={"error": "invalid_generated_citation", "message": "No se pudo validar la respuesta."},
        ) from None
    except Exception:
        logger.error("question processing failed")
        raise HTTPException(
            status_code=502,
            detail={"error": "answer_generation_failed", "message": "No se pudo procesar la consulta."},
        ) from None

    return AskResponse(
        answer=answer.answer,
        references=list(answer.references),
        evidence=[
            EvidenceResponse(reference=item.reference, text=item.text)
            for item in answer.evidence
        ],
        disclaimer=answer.disclaimer,
        abstained=answer.abstained,
    )


@router.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
def health(request: Request) -> HealthResponse:
    if request.app.state.answer_service is not None:
        return HealthResponse(status="ok", index_ready=True)
    index_ready = bool(request.app.state.index_ready())
    if not index_ready:
        raise HTTPException(
            status_code=503,
            detail={"status": "unavailable", "index_ready": False},
        )
    return HealthResponse(status="ok", index_ready=True)


def sanitize_validation_error(_: Request, exc: RequestValidationError) -> Any:
    """Return request validation errors without echoing submitted question contents."""
    return {"error": "invalid_request", "message": "La pregunta o los parámetros no son válidos."}
