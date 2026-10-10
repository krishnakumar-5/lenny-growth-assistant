from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse
from app.db.session import check_db_connection

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns current service health, environment, timestamp, version, and database connectivity.",
)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return health status, active environment, current version, UTC timestamp, and database status."""
    db_connected = check_db_connection()
    db_status = "connected" if db_connected else "unavailable"

    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        database=db_status,
    )
