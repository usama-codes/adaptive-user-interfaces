from fastapi import FastAPI

from adaptive_ui_service.app.core.config import settings
from adaptive_ui_service.app.routes.health import router as health_router

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health_router)
