from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.schemas.health import RootResponse
from app.api.routes import api_router

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS middleware configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 router under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    response_model=RootResponse,
    tags=["root"],
    summary="Root Endpoint",
    description="Returns application name, version, status, and docs URL.",
)
def read_root() -> RootResponse:
    """Return application name, version, and server status."""
    return RootResponse(
        name=settings.PROJECT_NAME,
        version=settings.VERSION,
        status="running",
        docs_url="/docs",
    )
