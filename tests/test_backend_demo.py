import io
import json
from unittest.mock import Mock

import pytest

import app as careergrid_app
import routes.careers as career_routes
import routes.interviews as interview_routes
import routes.simulations as simulation_routes
from services.simulation.career_service import get_company_display_name
from services.simulation.backend_demo_interview_service import (
    get_backend_demo_interview,
)
from services.simulation.backend_demo_scenario_service import (
    BACKEND_DEMO_COMPANY_ID,
    BACKEND_DEMO_JOB_SOURCE,
    get_backend_demo_workplace_scenario,
)
from services.ai.interview_service import INTERVIEW_QUESTION_COUNT
from services.ai.scenario_generation_service import validate_workplace_scenario
from services.simulation.simulation_storage import save_workplace_scenario


@pytest.fixture
def client():
    careergrid_app.app.config.update(TESTING=True)

    with careergrid_app.app.test_client() as test_client:
        with test_client.session_transaction() as user_session:
            user_session["user_id"] = "demo-user"
            user_session["user_email"] = "demo@example.com"
            user_session["user_name"] = "Demo User"

        yield test_client


def _demo_form(**overrides):
    form = {
        "career_id": "software-developer",
        "position_id": "backend-developer",
        "company_id": BACKEND_DEMO_COMPANY_ID,
        "job_source": BACKEND_DEMO_JOB_SOURCE,
    }
    form.update(overrides)
    return form


def _completed_attempt(company_id=BACKEND_DEMO_COMPANY_ID):
    return {
        "simulation_mode": "workplace",
        "career_id": "software-developer",
        "position_id": "backend-developer",
        "company_id": company_id,
        "status": "completed",
        "evaluation": {"overall_score": 90},
        "public_scenario": {},
        "responses": {},
    }


def _project_file(scenario, path):
    return next(
        file_item["content"]
        for file_item in scenario["public_scenario"]["project"]["files"]
        if file_item["path"] == path
    )


def test_backend_companies_page_shows_demo_before_live_jobs(client, monkeypatch):
    monkeypatch.setattr(
        career_routes,
        "fetch_adzuna_jobs",
        lambda *args, **kwargs: [
            {
                "title": "Live Backend Position",
                "company": {"display_name": "Live Company"},
                "location": {"display_name": "Remote"},
                "description": "Live Adzuna listing",
                "redirect_url": "https://example.com/job",
            }
        ],
    )

    response = client.get(
        "/api/careers/software-developer/positions/backend-developer/companies"
    )
    companies = response.get_json()["companies"]

    assert response.status_code == 200
    assert companies[0]["company_id"] == "careergrid-demo"
    assert companies[0]["job_source"] == "backend_demo"
    assert companies[1]["title"] == "Live Backend Position"


def test_frontend_companies_page_does_not_offer_backend_demo(client, monkeypatch):
    monkeypatch.setattr(
        career_routes,
        "fetch_adzuna_jobs",
        lambda *args, **kwargs: [],
    )

    response = client.get(
        "/api/careers/software-developer/positions/frontend-developer/companies"
    )
    companies = response.get_json()["companies"]

    assert response.status_code == 200
    assert all(company["company_id"] != "careergrid-demo" for company in companies)
    assert all(company["job_source"] != "backend_demo" for company in companies)


def test_demo_start_uses_predefined_scenario_without_gemini(client, monkeypatch):
    saved = {}
    monkeypatch.setattr(
        simulation_routes,
        "create_workplace_simulation_attempt",
        lambda **kwargs: "attempt-demo",
    )
    monkeypatch.setattr(
        simulation_routes,
        "generate_workplace_scenario",
        Mock(side_effect=AssertionError("Gemini generator must not be called")),
    )
    monkeypatch.setattr(
        simulation_routes,
        "save_workplace_scenario",
        lambda **kwargs: saved.update(kwargs),
    )

    response = client.post(
        "/simulation/workplace/start",
        data=_demo_form(),
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/workspace/attempt/attempt-demo"
    )
    assert saved["public_scenario"]["scenario_id"] == (
        "technova-user-profile-availability-v2"
    )
    assert {change["path"] for change in saved["private_context"]["expected_changes"]} == {
        "app.py",
        "services/user_service.py",
    }
    assert saved["generation_source"] == "predefined_demo"
    assert saved["generation_attempt_count"] == 1


def test_predefined_workplace_scenario_passes_existing_validator():
    scenario = get_backend_demo_workplace_scenario(attempt_id="validator-test")

    validated = validate_workplace_scenario(scenario)

    assert validated == scenario
    assert validated["public_scenario"]["project"]["name"] == (
        "user-profile-service"
    )


def test_demo_public_evidence_contains_both_reported_cases():
    scenario = get_backend_demo_workplace_scenario(attempt_id="evidence-test")
    task = scenario["public_scenario"]["task"]
    evidence = scenario["public_scenario"]["resources"][0]["content"]

    assert task["subject"] == "Production issue — User Profile API"
    assert "user IDs that do not exist" in task["body"]
    assert "deactivated account is still accessible" in task["body"]
    assert evidence.count("Case ") == 2
    assert "GET /api/users/1842" in evidence
    assert "Expected: 404 Not Found" in evidence
    assert "Actual: 500 Internal Server Error" in evidence
    assert "TypeError: 'NoneType' object is not subscriptable" in evidence
    assert "GET /api/users/103" in evidence
    assert "Actual: 200 OK" in evidence


def test_demo_dataset_contains_active_and_inactive_users():
    scenario = get_backend_demo_workplace_scenario(attempt_id="dataset-test")
    users = json.loads(_project_file(scenario, "data/users.json"))

    assert any(user["active"] is True for user in users)
    assert any(
        user["id"] == 103
        and user["name"] == "Daniel Reed"
        and user["active"] is False
        for user in users
    )


def test_demo_public_scenario_does_not_reveal_the_two_fixes():
    scenario = get_backend_demo_workplace_scenario(attempt_id="privacy-test")
    public_payload = json.dumps(scenario["public_scenario"])

    assert "if user is None" not in public_payload
    assert 'user.get(\\"active\\", True)' not in public_payload
    assert "filter inactive users" not in public_payload.lower()
    assert "root_cause" not in public_payload
    assert "expected_changes" not in public_payload


def test_demo_private_context_covers_both_causes_and_required_changes():
    scenario = get_backend_demo_workplace_scenario(attempt_id="rubric-test")
    private = scenario["private_context"]
    root_cause = private["root_cause"].lower()
    expectations = {
        change["path"]: change["expectation"].lower()
        for change in private["expected_changes"]
    }

    assert "returns none" in root_cause
    assert "without guarding" in root_cause
    assert "matches only by id" in root_cause
    assert "deactivated user 103" in root_cause
    assert set(expectations) == {"app.py", "services/user_service.py"}
    assert "http 404" in expectations["app.py"]
    assert "deactivated users" in expectations["services/user_service.py"]
    assert "active users" in expectations["services/user_service.py"]


def test_demo_verification_expectations_cover_all_three_profiles():
    scenario = get_backend_demo_workplace_scenario(attempt_id="verification-test")
    verification = " ".join(
        scenario["private_context"]["verification_expectations"]
    ).lower()

    assert "active user 101" in verification and "http 200" in verification
    assert "nonexistent user 1842" in verification and "http 404" in verification
    assert "deactivated user 103" in verification and "http 404" in verification
    assert "no inactive profile data is exposed" in verification


def test_normal_backend_start_still_uses_gemini_generator(client, monkeypatch):
    scenario = get_backend_demo_workplace_scenario(attempt_id="normal-test")
    generated = Mock(return_value=(scenario, 2))
    saved = {}
    monkeypatch.setattr(
        simulation_routes,
        "create_workplace_simulation_attempt",
        lambda **kwargs: "attempt-normal",
    )
    monkeypatch.setattr(
        simulation_routes,
        "generate_workplace_scenario",
        generated,
    )
    monkeypatch.setattr(
        simulation_routes,
        "get_backend_demo_workplace_scenario",
        Mock(side_effect=AssertionError("Demo scenario must not be used")),
    )
    monkeypatch.setattr(
        simulation_routes,
        "save_workplace_scenario",
        lambda **kwargs: saved.update(kwargs),
    )

    response = client.post(
        "/simulation/workplace/start",
        data={
            "career_id": "software-developer",
            "position_id": "backend-developer",
            "company_id": "technova",
            "job_source": "demo",
        },
    )

    assert response.status_code == 302
    generated.assert_called_once_with(
        career_id="software-developer",
        position_id="backend-developer",
        company_id="technova",
        attempt_id="attempt-normal",
    )
    assert saved["generation_source"] == "gemini"


def test_frontend_start_still_uses_its_dedicated_generator(client, monkeypatch):
    frontend_scenario = {
        "public_scenario": {"scenario_id": "frontend-existing-flow"},
        "private_context": {"rubric": "existing"},
    }
    frontend_generator = Mock(return_value=(frontend_scenario, 1))
    monkeypatch.setattr(
        simulation_routes,
        "create_workplace_simulation_attempt",
        lambda **kwargs: "attempt-frontend",
    )
    monkeypatch.setattr(
        simulation_routes,
        "generate_frontend_workplace_scenario",
        frontend_generator,
    )
    monkeypatch.setattr(
        simulation_routes,
        "generate_workplace_scenario",
        Mock(side_effect=AssertionError("Generic Backend generator must not run")),
    )
    monkeypatch.setattr(
        simulation_routes,
        "get_backend_demo_workplace_scenario",
        Mock(side_effect=AssertionError("Backend demo scenario must not run")),
    )
    monkeypatch.setattr(
        simulation_routes,
        "save_workplace_scenario",
        Mock(),
    )

    response = client.post(
        "/simulation/workplace/start",
        data={
            "career_id": "software-developer",
            "position_id": "frontend-developer",
            "company_id": "pixelworks",
            "job_source": "demo",
        },
    )

    assert response.status_code == 302
    frontend_generator.assert_called_once_with(
        company_name="PixelWorks",
        attempt_id="attempt-frontend",
    )


def test_demo_attempt_uses_predefined_interview_without_gemini(client, monkeypatch):
    created = {}
    monkeypatch.setattr(
        interview_routes,
        "get_simulation_attempt",
        lambda **kwargs: _completed_attempt(),
    )
    monkeypatch.setattr(
        interview_routes,
        "generate_interview_questions",
        Mock(side_effect=AssertionError("Gemini question generation must not run")),
    )
    monkeypatch.setattr(
        interview_routes,
        "create_interview_attempt",
        lambda **kwargs: created.update(kwargs) or "interview-demo",
    )

    response = client.post(
        "/simulation/attempts/attempt-demo/interview/start"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/interview/interview-demo"
    )
    assert len(created["interview_data"]["public_questions"]) == 4
    assert created["interview_data"]["public_questions"][0]["question"] == (
        "Tell me about yourself and what interests you about backend development."
    )


def test_workplace_report_api_preserves_retry_source_and_interview_unlock(
    client,
    monkeypatch,
):
    attempt = _completed_attempt()
    attempt["public_scenario"] = {
        "task": {"subject": "User Profile API Production Incident"}
    }
    monkeypatch.setattr(
        simulation_routes,
        "get_simulation_attempt",
        lambda **kwargs: attempt,
    )

    response = client.get("/api/simulation/attempts/attempt-demo/report")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["job_source"] == BACKEND_DEMO_JOB_SOURCE
    assert payload["interview_unlocked"] is True


def test_normal_attempt_still_calls_gemini_interview_generation(client, monkeypatch):
    generated_interview = get_backend_demo_interview()
    generator = Mock(return_value=generated_interview)
    monkeypatch.setattr(
        interview_routes,
        "get_simulation_attempt",
        lambda **kwargs: _completed_attempt(company_id="technova"),
    )
    monkeypatch.setattr(
        interview_routes,
        "generate_interview_questions",
        generator,
    )
    monkeypatch.setattr(
        interview_routes,
        "get_backend_demo_interview",
        Mock(side_effect=AssertionError("Demo interview must not be used")),
    )
    monkeypatch.setattr(
        interview_routes,
        "create_interview_attempt",
        lambda **kwargs: "interview-normal",
    )

    response = client.post(
        "/simulation/attempts/attempt-normal/interview/start"
    )

    assert response.status_code == 302
    generator.assert_called_once()
    assert generator.call_args.kwargs["company_name"] == "TechNova"


def test_demo_interview_has_four_exact_questions_and_matching_private_rubrics():
    interview = get_backend_demo_interview()
    question_ids = {str(question["id"]) for question in interview["public_questions"]}
    expected_questions = [
        "Tell me about yourself and what interests you about backend development.",
        "Tell me about a project you worked on that you're proud of. What was your role, what technologies did you use, and what challenges did you face?",
        "Tell me about a time you faced a technical problem that you did not immediately know how to solve. How did you approach it?",
        "A backend service suddenly starts returning unexpected 500 errors in production. Walk me through how you would investigate the issue before making a code change.",
    ]

    assert len(interview["public_questions"]) == 4
    assert [
        question["question"] for question in interview["public_questions"]
    ] == expected_questions
    assert [
        question["category"] for question in interview["public_questions"]
    ] == ["introduction", "project_experience", "behavioral", "problem_solving"]
    assert [
        question["target_words"] for question in interview["public_questions"]
    ] == [90, 140, 130, 150]
    assert len(interview["private_rubrics"]) == 4
    assert question_ids == set(interview["private_rubrics"])


def test_demo_public_questions_do_not_expose_private_rubrics():
    interview = get_backend_demo_interview()

    assert all(
        set(question) == {
            "id",
            "category",
            "question",
            "difficulty",
            "target_words",
            "time_limit_seconds",
        }
        for question in interview["public_questions"]
    )
    assert all("rubric" not in question for question in interview["public_questions"])


def test_private_rubrics_are_not_rendered_in_interview_browser_page(
    client,
    monkeypatch,
):
    interview = get_backend_demo_interview()
    interview.update(
        {
            "status": "in_progress",
            "career_id": "software-developer",
            "position_id": "backend-developer",
            "company_id": BACKEND_DEMO_COMPANY_ID,
            "answers": {},
            "current_question": 1,
        }
    )
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: interview,
    )

    response = client.get("/api/interview/interview-demo")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["questions"][0]["question"] == interview["public_questions"][0]["question"]
    assert payload["current_question"] == 1
    serialized = response.get_data(as_text=True)
    assert "excellent_answer_should_include" not in serialized
    assert "Cannot identify a project or personal contribution" not in serialized


def test_fourth_demo_answer_completes_interview_using_actual_question_count(
    client,
    monkeypatch,
):
    interview = get_backend_demo_interview()
    interview.update(
        {
            "status": "in_progress",
            "career_id": "software-developer",
            "position_id": "backend-developer",
            "company_id": BACKEND_DEMO_COMPANY_ID,
            "answers": {
                "1": {"transcript": "Answer one"},
                "2": {"transcript": "Answer two"},
                "3": {"transcript": "Answer three"},
            },
            "current_question": 4,
        }
    )
    refreshed = dict(interview)
    refreshed["answers"] = {
        **interview["answers"],
        "4": {"transcript": "Answer four", "question_score": 84},
    }
    get_attempt = Mock(side_effect=[interview, refreshed])
    final_evaluation = Mock(
        return_value={
            "overall_score": 84,
            "strengths": [],
            "areas_for_improvement": [],
            "next_steps": [],
        }
    )
    complete_attempt = Mock()
    monkeypatch.setattr(interview_routes, "get_interview_attempt", get_attempt)
    monkeypatch.setattr(
        interview_routes,
        "analyze_spoken_answer",
        Mock(return_value={"question_score": 84, "transcript": "Answer four"}),
    )
    monkeypatch.setattr(interview_routes, "save_interview_answer", Mock())
    monkeypatch.setattr(
        interview_routes,
        "generate_final_interview_evaluation",
        final_evaluation,
    )
    monkeypatch.setattr(
        interview_routes,
        "complete_interview_attempt",
        complete_attempt,
    )

    response = client.post(
        "/api/interview/interview-demo/answer",
        data={
            "question_id": "4",
            "duration_seconds": "45",
            "audio": (io.BytesIO(b"demo audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json()["completed"] is True
    assert response.get_json()["review_url"] == "/interview/interview-demo/review"
    assert len(final_evaluation.call_args.kwargs["questions"]) == 4
    complete_attempt.assert_called_once()


def test_interview_storage_failure_does_not_expose_internal_exception(
    client,
    monkeypatch,
):
    interview = get_backend_demo_interview()
    interview.update(
        {
            "status": "in_progress",
            "career_id": "software-developer",
            "position_id": "backend-developer",
            "company_id": BACKEND_DEMO_COMPANY_ID,
            "answers": {},
            "current_question": 1,
        }
    )
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: interview,
    )
    monkeypatch.setattr(
        interview_routes,
        "analyze_spoken_answer",
        Mock(return_value={"question_score": 75, "transcript": "Answer"}),
    )
    monkeypatch.setattr(
        interview_routes,
        "save_interview_answer",
        Mock(side_effect=RuntimeError("private database detail")),
    )

    response = client.post(
        "/api/interview/interview-demo/answer",
        data={
            "question_id": "1",
            "duration_seconds": "20",
            "audio": (io.BytesIO(b"demo audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    message = response.get_json()["error"]
    assert message == "Could not save your interview answer. Please try again."
    assert "private database detail" not in message


def test_normal_interview_question_count_remains_seven():
    assert INTERVIEW_QUESTION_COUNT == 7


@pytest.mark.parametrize(
    ("provided_source", "expected_source"),
    [(None, "gemini"), ("predefined_demo", "predefined_demo")],
)
def test_workplace_storage_preserves_default_and_custom_generation_sources(
    monkeypatch,
    provided_source,
    expected_source,
):
    class AttemptReference:
        def __init__(self):
            self.updated = None

        def get(self):
            return {"simulation_mode": "workplace"}

        def update(self, value):
            self.updated = value

    reference = AttemptReference()
    monkeypatch.setattr(
        "services.simulation.simulation_storage.get_database_reference",
        lambda path: reference,
    )
    arguments = {
        "user_id": "demo-user",
        "attempt_id": "attempt-source",
        "public_scenario": {"scenario_id": "public"},
        "private_context": {"root_cause": "private"},
        "generation_attempt_count": 1,
    }
    if provided_source is not None:
        arguments["generation_source"] = provided_source

    save_workplace_scenario(**arguments)

    assert reference.updated["generation"]["source"] == expected_source


@pytest.mark.parametrize(
    "invalid_form",
    [
        _demo_form(position_id="frontend-developer"),
        _demo_form(company_id="technova"),
        _demo_form(career_id="ui-ux-designer", position_id="ux-designer"),
    ],
)
def test_invalid_backend_demo_source_combinations_are_rejected(
    client,
    monkeypatch,
    invalid_form,
):
    create_attempt = Mock(
        side_effect=AssertionError("Invalid demo request created an attempt")
    )
    monkeypatch.setattr(
        simulation_routes,
        "create_workplace_simulation_attempt",
        create_attempt,
    )

    response = client.post(
        "/simulation/workplace/start",
        data=invalid_form,
    )

    assert response.status_code == 302
    create_attempt.assert_not_called()


def test_demo_company_display_name_is_consistent():
    assert get_company_display_name(
        "software-developer",
        "backend-developer",
        BACKEND_DEMO_COMPANY_ID,
    ) == "TechNova"
