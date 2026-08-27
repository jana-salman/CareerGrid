"""Contracts for the React-facing Flask API foundation."""

import pytest

from app import create_app


@pytest.fixture
def client():
    application = create_app(
        {"TESTING": True, "SECRET_KEY": "api-foundation-test-key"}
    )
    with application.test_client() as test_client:
        yield test_client


def test_health_endpoint_is_public_and_browser_safe(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "service": "careergrid",
        "status": "ok",
    }
