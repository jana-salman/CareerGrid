"""Contracts for React-facing career selection data."""

import pytest

from app import create_app


@pytest.fixture
def client():
    application = create_app(
        {"TESTING": True, "SECRET_KEY": "career-catalog-api-test-key"}
    )
    with application.test_client() as test_client:
        with test_client.session_transaction() as user_session:
            user_session["user_id"] = "career-catalog-user"
            user_session["user_email"] = "career-catalog@example.com"
        yield test_client


def test_career_catalog_preserves_coming_soon_state(client):
    response = client.get("/api/careers")

    assert response.status_code == 200
    careers = {career["id"]: career for career in response.get_json()["careers"]}
    assert careers["software-developer"]["available"] is True
    assert careers["data-analyst"]["available"] is False


def test_position_catalog_uses_service_owned_metadata(client):
    response = client.get("/api/careers/software-developer/positions")

    assert response.status_code == 200
    assert response.get_json()["positions"] == [
        {"id": "backend-developer", "title": "Backend Developer", "available": True},
        {"id": "frontend-developer", "title": "Frontend Developer", "available": True},
    ]


def test_company_catalog_keeps_demo_and_fallback_behavior(client, monkeypatch):
    monkeypatch.setattr("routes.careers.fetch_adzuna_jobs", lambda *args, **kwargs: [])

    response = client.get(
        "/api/careers/software-developer/positions/backend-developer/companies"
    )

    assert response.status_code == 200
    companies = response.get_json()["companies"]
    assert companies[0]["job_source"] == "backend_demo"
    assert companies[0]["company_id"] == "careergrid-demo"
    assert {company["company_id"] for company in companies[1:]} == {
        "technova",
        "brightsoft",
    }


def test_unavailable_company_catalog_is_not_exposed(client):
    response = client.get(
        "/api/careers/data-analyst/positions/data-analyst/companies"
    )

    assert response.status_code == 404
