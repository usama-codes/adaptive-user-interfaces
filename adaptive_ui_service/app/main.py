from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from adaptive_ui_service.app.core import exceptions, logging_config
from adaptive_ui_service.app.core.config import settings
from adaptive_ui_service.app.models.capability import load_manifest
from adaptive_ui_service.app.routes.health import router as health_router
from adaptive_ui_service.app.routes.intent import router as intent_router
from adaptive_ui_service.app.services.retrieval_service import RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    capabilities = load_manifest()
    try:
        retrieval_service = RetrievalService.from_artifacts(
            index_dir=settings.index_dir,
            capabilities=capabilities,
            model_name=settings.embedding_model_name,
        )
    except exceptions.IndexNotFoundError:
        logger.warning(
            "Retrieval index not found; run `python -m scripts.build_index` "
            "to enable capability retrieval"
        )
        retrieval_service = RetrievalService.empty()

    app.state.retrieval_service = retrieval_service
    yield


def get_retrieval_service(request: Request) -> RetrievalService:
    return request.app.state.retrieval_service


def create_app() -> FastAPI:
    logging_config.configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(logging_config.RequestLoggingMiddleware)
    app.add_exception_handler(exceptions.APIError, exceptions.api_error_handler)
    app.add_exception_handler(Exception, exceptions.unhandled_exception_handler)
    app.include_router(health_router)
    app.include_router(intent_router)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        _request: Request,
        exception: HTTPException,
    ) -> JSONResponse:
        content = (
            exception.detail
            if isinstance(exception.detail, dict)
            else {
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exception.detail),
                }
            }
        )

        return JSONResponse(
            status_code=exception.status_code,
            content=content,
            headers=exception.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        _request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exception.errors(),
                }
            },
        )

    return app


app = create_app()
