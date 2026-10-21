"""FastAPI application factory with lazy local model initialization."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import chromadb
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from consulta_ai_act.answer_service import AnswerService
from consulta_ai_act.api.routes import router, sanitize_validation_error
from consulta_ai_act.config import Settings
from consulta_ai_act.generation.answer_generator import AnswerGenerator
from consulta_ai_act.generation.citation_validator import CitationValidator
from consulta_ai_act.logging_config import configure_logging
from consulta_ai_act.retrieval.retriever import RegulationRetriever
from consulta_ai_act.retrieval.vector_store import ChromaVectorStore, SentenceTransformerEmbedder


def create_app(
    *,
    settings: Settings | None = None,
    answer_service: Any | None = None,
    service_factory: Callable[[], AnswerService] | None = None,
    index_ready: Callable[[], bool] | None = None,
) -> FastAPI:
    """Create the API without loading embedding models until a request needs them."""
    active_settings = settings or Settings.from_env()
    configure_logging(active_settings.log_level)
    application = FastAPI(title="Consulta AI Act", version="0.1.0")
    application.state.settings = active_settings
    application.state.answer_service = answer_service
    application.state.service_factory = service_factory or (
        lambda: _build_answer_service(active_settings)
    )
    application.state.index_ready = index_ready or (
        lambda: _is_index_ready(active_settings.chroma_path)
    )
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        content = await sanitize_validation_error(request, exc)
        return JSONResponse(status_code=422, content=content)

    @application.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            content = exc.detail
        else:
            content = {"error": "request_failed", "message": "No se pudo procesar la solicitud."}
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    return application


def _build_answer_service(settings: Settings) -> AnswerService:
    """Load only the configured local index and construct the generation pipeline."""
    if not settings.chroma_path.exists():
        raise FileNotFoundError("Vector index does not exist")
    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    store = ChromaVectorStore(settings.chroma_path, embedder)
    if store.count == 0:
        raise FileNotFoundError("Vector index is empty")
    retriever = RegulationRetriever(store, settings)
    generator = AnswerGenerator(settings)
    return AnswerService(retriever, generator, CitationValidator())


def _is_index_ready(path: Path) -> bool:
    """Check local Chroma readiness without loading the embedding or LLM model."""
    if not path.exists():
        return False
    try:
        client = chromadb.PersistentClient(path=str(path))
        collection = client.get_collection("ai_act_es")
        return collection.count() > 0
    except Exception:
        return False


app = create_app()