from fastapi import APIRouter, status

from src.app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/healthz", status_code=status.HTTP_200_OK)
def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
    }


@router.get("/readyz", status_code=status.HTTP_200_OK)
def readiness_check():
    return {"status": "ready"}
