from unittest.mock import Mock

import app as careergrid_app
import routes.simulations as simulation_routes
from services.simulation_storage import get_user_visible_evaluation


def test_readiness_is_part_of_public_report_but_unknown_fields_are_not():
    public = get_user_visible_evaluation(
        {
            "overall_score": 80,
            "summary": "Good",
            "frontend_readiness": "Ready",
            "private_notes": "secret",
        }
    )
    assert public["frontend_readiness"] == "Ready"
    assert "private_notes" not in public


def test_public_attempt_api_never_returns_private_context(monkeypatch):
    get_attempt = Mock(
        return_value={
            "simulation_mode": "workplace",
            "career_id": "software-developer",
            "position_id": "frontend-developer",
            "company_id": "pixelworks",
            "status": "in_progress",
            "public_scenario": {"scenario_id": "frontend-attempt"},
            "private_context": {
                "root_cause": "server-only",
                "expected_patch": {"product_js": "server-only"},
            },
        }
    )
    monkeypatch.setattr(simulation_routes, "get_simulation_attempt", get_attempt)
    careergrid_app.app.config.update(TESTING=True)

    with careergrid_app.app.test_client() as client:
        with client.session_transaction() as user_session:
            user_session["user_id"] = "frontend-user"
            user_session["user_email"] = "frontend@example.com"

        response = client.get("/api/simulation/attempts/attempt-1")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["public_scenario"] == {"scenario_id": "frontend-attempt"}
    assert "private_context" not in payload
    assert "root_cause" not in response.get_data(as_text=True)
    get_attempt.assert_called_once_with(
        user_id="frontend-user",
        attempt_id="attempt-1",
    )

