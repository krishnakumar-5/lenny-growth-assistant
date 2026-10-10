from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Structured response model for service health check."""

    status: str = Field(default="healthy", description="Current service health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="Current application version")
    database: str = Field(
        default="unavailable",
        description="Database connectivity status ('connected' or 'unavailable')",
    )


class RootResponse(BaseModel):
    """Structured response model for the root endpoint."""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    status: str = Field(default="running", description="Status of the API server")
    docs_url: str = Field(default="/docs", description="Interactive API documentation URL")
