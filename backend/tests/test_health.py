from datetime import datetime
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()


def test_root_endpoint():
    """Verify that GET / returns application name, version, and running status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert data["status"] == "running"
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    """Verify that GET /api/v1/health returns structured health response."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["version"] == settings.VERSION
    assert "timestamp" in data
    assert "database" in data
    assert data["database"] in ["connected", "unavailable"]
    # Verify timestamp format is valid ISO
    parsed_time = datetime.fromisoformat(data["timestamp"])
    assert parsed_time is not None


def test_docs_endpoint():
    """Verify that GET /docs serves FastAPI Swagger documentation UI."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_openapi_json_endpoint():
    """Verify that openapi.json is served with expected API schema and title."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == settings.PROJECT_NAME
    assert data["info"]["version"] == settings.VERSION
    assert f"{settings.API_V1_STR}/health" in data["paths"]


def test_not_found_endpoint():
    """Verify that requests to non-existent endpoints return 404."""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
