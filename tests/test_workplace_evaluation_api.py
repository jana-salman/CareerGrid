from unittest.mock import Mock

from app import create_app
import routes.simulations as simulation_routes


def authenticated_client():
    application = create_app(
        {"TESTING": True, "SECRET_KEY": "workplace-evaluation-test-key"}
    )
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["user_id"] = "evaluation-user"
        user_session["user_email"] = "evaluation@example.com"
        user_session["user_name"] = "Zahraa"
    return client


def workplace_attempt(**overrides):
    attempt = {
        "simulation_mode": "workplace",
        "career_id": "software-developer",
        "position_id": "backend-developer",
        "company_id": "technova",
        "public_scenario": {
            "advisor": {"name": "Maya Chen"},
            "task": {"title": "Fix user lookup"},
        },
        "private_context": {"expected_changes": ["server-only"]},
        "evaluation": None,
    }
    attempt.update(overrides)
    return attempt


def test_repeated_evaluation_returns_saved_report_without_running_gemini(
    monkeypatch,
):
    evaluator = Mock(side_effect=AssertionError("Gemini must not run twice"))
    saver = Mock(side_effect=AssertionError("A saved report must not be saved twice"))
    monkeypatch.setattr(
        simulation_routes,
        "get_simulation_attempt",
        Mock(
            return_value=workplace_attempt(
                evaluation={
                    "overall_score": 87,
                    "summary": "Saved report",
                    "private_notes": "server-only",
                }
            )
        ),
    )
    monkeypatch.setattr(
        simulation_routes, "evaluate_workplace_submission", evaluator
    )
    monkeypatch.setattr(simulation_routes, "save_simulation_evaluation", saver)

    response = authenticated_client().post(
        "/api/simulation/evaluation",
        json={"attempt_id": "attempt-1", "evidence": {"changed_files": []}},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "overall_score": 87,
        "summary": "Saved report",
    }
    evaluator.assert_not_called()
    saver.assert_not_called()


def test_evaluation_api_wraps_safe_client_evidence_with_server_context(
    monkeypatch,
):
    evaluator = Mock(return_value={"overall_score": 91, "summary": "Ready"})
    saver = Mock(return_value={"overall_score": 91, "summary": "Ready"})
    monkeypatch.setattr(
        simulation_routes,
        "get_simulation_attempt",
        Mock(return_value=workplace_attempt()),
    )
    monkeypatch.setattr(
        simulation_routes, "evaluate_workplace_submission", evaluator
    )
    monkeypatch.setattr(simulation_routes, "save_simulation_evaluation", saver)
    client_evidence = {
        "changed_files": [
            {"path": "app.py", "before": "old", "after": "new"}
        ],
        "submission": {"pullRequestId": 1},
    }

    response = authenticated_client().post(
        "/api/simulation/evaluation",
        json={"attempt_id": "attempt-1", "evidence": client_evidence},
    )

    assert response.status_code == 200
    wrapped = evaluator.call_args.args[0]
    assert wrapped["actual_user_evidence"] == client_evidence
    assert wrapped["private_expected_solution"] == {
        "expected_changes": ["server-only"]
    }
    assert wrapped["participant_context"] == {
        "advisor_name": "Maya Chen",
        "student_display_name": "Zahraa",
    }
    assert "private_expected_solution" not in response.get_data(as_text=True)
    saver.assert_called_once_with(
        user_id="evaluation-user",
        attempt_id="attempt-1",
        evaluation={"overall_score": 91, "summary": "Ready"},
    )
