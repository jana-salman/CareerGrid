"""Honest job-provider states, including Lebanon handling."""

from unittest.mock import Mock

import pytest
import requests

import services.simulation.job_service as job_service
from app import create_app


def _response(payload):
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value=payload)
    return response


ADZUNA_JOB = {
    "title": "Backend Developer",
    "company": {"display_name": "Acme"},
    "location": {"display_name": "London"},
    "description": "<p>Build APIs</p>",
    "redirect_url": "https://www.adzuna.co.uk/jobs/land/ad/1",
    "created": "2026-11-01T00:00:00Z",
}


def test_adzuna_uses_the_selected_supported_country_and_keeps_listing_links(monkeypatch):
    get = Mock(return_value=_response({"results": [ADZUNA_JOB]}))
    monkeypatch.setattr(job_service.requests, "get", get)
    result = job_service.search_jobs("Backend Developer", country="gb", adzuna_app_id="id", adzuna_app_key="key")
    assert get.call_args.args[0] == "https://api.adzuna.com/v1/api/jobs/gb/search/1"
    assert result["status"] == "ok"
    job = result["jobs"][0]
    assert job["url"] == "https://www.adzuna.co.uk/jobs/land/ad/1"
    assert job["location"] == "London"
    assert job["source_label"] == "Adzuna"
    assert job["description"] == "Build APIs"
    assert result["attribution"]["label"] == "Jobs by Adzuna"


def test_lebanon_is_never_sent_to_adzuna_and_is_reported_unsupported_without_a_provider(monkeypatch):
    get = Mock(side_effect=AssertionError("Adzuna must not be queried for Lebanon"))
    post = Mock(side_effect=AssertionError("No Lebanon provider is configured"))
    monkeypatch.setattr(job_service.requests, "get", get)
    monkeypatch.setattr(job_service.requests, "post", post)
    result = job_service.search_jobs("Backend Developer", country="lb", adzuna_app_id="id", adzuna_app_key="key")
    assert result["status"] == "unsupported_location"
    assert result["jobs"] == []
    assert "Adzuna does not cover Lebanon" in result["message"]


def test_lebanon_provider_keeps_only_listings_located_in_lebanon(monkeypatch):
    post = Mock(return_value=_response({"jobs": [
        {"title": "Backend Dev", "company": "Cedar Tech", "location": "Beirut, Lebanon", "snippet": "APIs", "link": "https://jooble.org/desc/1"},
        {"title": "Backend Dev", "company": "Elsewhere", "location": "Dubai", "snippet": "APIs", "link": "https://jooble.org/desc/2"},
    ]}))
    monkeypatch.setattr(job_service.requests, "post", post)
    result = job_service.search_jobs("Backend Developer", country="lb", jooble_api_key="secret")
    assert post.call_args.args[0] == "https://jooble.org/api/secret"
    assert result["status"] == "ok"
    assert [job["company_name"] for job in result["jobs"]] == ["Cedar Tech"]
    assert result["jobs"][0]["source_label"] == "Jooble"


def test_no_results_provider_errors_and_missing_keys_are_distinct(monkeypatch):
    monkeypatch.setattr(job_service.requests, "get", Mock(return_value=_response({"results": []})))
    assert job_service.search_jobs("X", country="us", adzuna_app_id="i", adzuna_app_key="k")["status"] == "no_results"

    monkeypatch.setattr(job_service.requests, "get", Mock(side_effect=requests.exceptions.Timeout()))
    assert job_service.search_jobs("X", country="us", adzuna_app_id="i", adzuna_app_key="k")["status"] == "provider_error"

    assert job_service.search_jobs("X", country="us")["status"] == "not_configured"
    assert job_service.search_jobs("X", country="zz")["status"] == "unsupported_location"
    assert job_service.search_jobs("X", country="../us")["status"] == "unsupported_location"


@pytest.fixture
def client():
    application = create_app({"TESTING": True, "SECRET_KEY": "jobs", "ADZUNA_APP_ID": None, "ADZUNA_APP_KEY": None, "JOOBLE_API_KEY": None})
    test_client = application.test_client()
    with test_client.session_transaction() as user_session:
        user_session["user_id"] = "u"
        user_session["user_email"] = "u@example.com"
    return test_client


def test_company_api_reports_lebanon_honestly_and_offers_labelled_practice_options(client):
    response = client.get("/api/careers/software-developer/positions/frontend-developer/companies?country=lb")
    data = response.get_json()
    assert response.status_code == 200
    assert data["job_search"]["status"] == "unsupported_location"
    assert {"code": "lb", "name": "Lebanon", "provider": "jooble"} in data["job_search"]["supported_countries"]
    assert data["companies"], "practice options remain available"
    assert all(card["listing_kind"] == "practice" for card in data["companies"])
    assert all("not a live vacancy" in card["description"] for card in data["companies"])
    assert "key" not in str(data["job_search"]).lower().replace("jobs by", "")
