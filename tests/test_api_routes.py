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


def test_anonymous_session_request_returns_json_unauthorized(client):
    response = client.get("/api/auth/session")

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json() == {
        "authenticated": False,
        "error": "Authentication required.",
    }


def test_anonymous_existing_protected_api_returns_json_unauthorized(client):
    response = client.get("/api/simulation/attempts/example-attempt")

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()["error"] == "Authentication required."


def test_anonymous_interview_workspace_and_review_apis_are_protected(client):
    workspace_response = client.get("/api/interview/interview-id")
    review_response = client.get("/api/interview/interview-id/review")

    for response in (workspace_response, review_response):
        assert response.status_code == 401
        assert response.get_json() == {
            "authenticated": False,
            "error": "Authentication required.",
        }


def test_authenticated_session_returns_only_browser_safe_identity(client):
    with client.session_transaction() as user_session:
        user_session["user_id"] = "user-123"
        user_session["user_email"] = "student@example.com"
        user_session["user_name"] = "Student User"

    response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.get_json() == {
        "authenticated": True,
        "user": {
            "email": "student@example.com",
            "id": "user-123",
            "name": "Student User",
        },
    }
