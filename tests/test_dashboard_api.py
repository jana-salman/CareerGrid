"""Dashboard API response and Firebase access regression coverage."""

from app import create_app
from constants import WORKPLACE_SIMULATION_MODE
import routes.dashboard as dashboard_routes


def _authenticated_client():
    app = create_app(
        {
            "SECRET_KEY": "dashboard-test-secret",
            "TESTING": True,
        }
    )
    client = app.test_client()
    with client.session_transaction() as user_session:
        user_session["user_id"] = "dashboard-user"
        user_session["user_email"] = "dashboard@example.com"
        user_session["user_name"] = "Dashboard Student"
    return client


def test_dashboard_api_reads_the_authenticated_user_once_and_returns_a_compact_list(
    monkeypatch,
):
    calls = []

    def fake_list_attempts(user_id):
        calls.append(user_id)
        return [
            {
                "attempt_id": "workplace-1",
                "career_id": "software-engineer",
                "position_id": "backend-developer",
                "company_id": "techcorp",
                "simulation_mode": WORKPLACE_SIMULATION_MODE,
                "task_title": "Repair the profile API",
                "status": "completed",
                "completed_at": "2026-08-28T10:00:00+00:00",
                "evaluation": {
                    "overall_score": 88,
                    "summary": "A strong submission.",
                    "dimensions": {
                        "full_report_detail": {
                            "score": 88,
                        }
                    },
                },
            },
            {
                "attempt_id": "interview-1",
                "simulation_mode": "interview",
                "status": "completed",
            },
        ]

    monkeypatch.setattr(
        dashboard_routes,
        "list_user_simulation_attempts",
        fake_list_attempts,
    )

    response = _authenticated_client().get("/api/dashboard")

    assert response.status_code == 200
    assert calls == ["dashboard-user"]
    payload = response.get_json()
    assert payload["user_id"] == "dashboard-user"
    assert payload["user_name"] == "Dashboard Student"
    assert payload["simulation_count"] == 1
    assert payload["completed_count"] == 1
    assert payload["average_score"] == 88
    assert len(payload["attempts"]) == 1
    assert payload["attempts"][0]["has_evaluation"] is True
    assert payload["attempts"][0]["feedback_preview"] == "A strong submission."
    assert "evaluation" not in payload["attempts"][0]
