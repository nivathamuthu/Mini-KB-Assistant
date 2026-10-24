import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import ask, documents, health
from app.config import get_settings
from app.db import close_db, init_db
from app.errors import AppError, app_error_handler, error_payload, unhandled_error_handler
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    if settings.is_mock:
        logger.warning(
            "PROVIDER=mock: using demo-only mock embeddings and LLM. Not for production."
        )
    elif settings.llm_provider_name == "gemini":
        if settings.uses_local_embeddings:
            logger.info(
                "LLM google/gemini with local EMBED_MODEL=%s (dim=%s).",
                settings.embed_model,
                settings.embedding_dim,
            )
        else:
            logger.info("LLM google/gemini with Gemini API embeddings enabled.")
            if settings.embedding_dim != 768:
                logger.warning(
                    "Gemini API embeddings expect EMBEDDING_DIM=768 (current=%s). "
                    "Recreate the database after changing dimension.",
                    settings.embedding_dim,
                )
    await init_db(settings)
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Mini Knowledge Assistant", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request method=%s path=%s status=%s latency_ms=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            request_id,
        )
        return response

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        message = "Invalid request."
        if exc.errors():
            first = exc.errors()[0]
            msg = first.get("msg", "")
            if msg:
                message = msg
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", message, request_id),
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception("Database error request_id=%s", request_id)
        return JSONResponse(
            status_code=503,
            content=error_payload(
                "service_unavailable",
                "Service temporarily unavailable.",
                request_id,
            ),
        )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(ask.router)
    return app


app = create_app()
