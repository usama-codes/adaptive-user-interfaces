from fastapi import APIRouter

from adaptive_ui_service.app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}
