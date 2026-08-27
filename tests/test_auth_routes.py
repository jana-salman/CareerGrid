from unittest.mock import Mock

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app as careergrid_app
import routes.auth as auth_routes


@pytest.fixture
def client():
    careergrid_app.app.config.update(TESTING=True)
    with careergrid_app.app.test_client() as test_client:
        yield test_client


def test_anonymous_users_are_redirected_from_private_pages(client):
    dashboard_response = client.get("/dashboard")
    career_response = client.get("/career")

    assert dashboard_response.status_code == 302
    assert dashboard_response.headers["Location"].endswith("/login")
    assert career_response.status_code == 302
    assert career_response.headers["Location"].endswith("/")


def test_production_requires_an_explicit_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("CAREERGRID_ENV", "production")

    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        careergrid_app._secret_key()


def test_configured_secret_key_is_used_without_transformation(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-only-explicit-key")

    assert careergrid_app._secret_key() == "test-only-explicit-key"


def test_application_factory_registers_blueprints_and_accepts_overrides():
    application = careergrid_app.create_app(
        {"TESTING": True, "SECRET_KEY": "factory-test-key"}
    )

    endpoints = {rule.endpoint for rule in application.url_map.iter_rules()}

    assert application.config["TESTING"] is True
    assert application.config["SECRET_KEY"] == "factory-test-key"
    assert {
        "auth.login",
        "careers.career",
        "dashboard.dashboard",
        "simulations.start_workplace_simulation",
        "interviews.submit_interview_answer",
    } <= endpoints


def test_registration_normalizes_email_and_hashes_password(client, monkeypatch):
    create_user = Mock()
    monkeypatch.setattr(auth_routes, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(auth_routes, "create_user", create_user)

    response = client.post(
        "/register",
        data={
            "full_name": "Ada Student",
            "email": "  ADA@Example.COM  ",
            "password": "coursework-password",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login?registered=1")
    saved = create_user.call_args.kwargs
    assert saved["full_name"] == "Ada Student"
    assert saved["email"] == "ada@example.com"
    assert saved["password_hash"] != "coursework-password"
    assert check_password_hash(saved["password_hash"], "coursework-password")


def test_login_creates_only_the_expected_session_identity(client, monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda email: {
            "id": "user-123",
            "email": email,
            "full_name": "Ada Student",
            "password_hash": generate_password_hash("correct-password"),
        },
    )

    response = client.post(
        "/login",
        data={
            "email": "ADA@example.com",
            "password": "correct-password",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as user_session:
        assert dict(user_session) == {
            "user_email": "ada@example.com",
            "user_id": "user-123",
            "user_name": "Ada Student",
        }
