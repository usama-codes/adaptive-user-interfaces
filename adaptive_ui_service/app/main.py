from fastapi import FastAPI

from adaptive_ui_service.app.core import exceptions, logging_config
from adaptive_ui_service.app.core.config import settings
from adaptive_ui_service.app.routes.health import router as health_router


def create_app() -> FastAPI:
    logging_config.configure_logging()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(logging_config.RequestLoggingMiddleware)
    app.add_exception_handler(exceptions.APIError, exceptions.api_error_handler)
    app.add_exception_handler(Exception, exceptions.unhandled_exception_handler)
    app.include_router(health_router)
    return app


app = create_app()
