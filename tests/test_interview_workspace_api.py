"""Browser-safe API contracts for the React interview workspace."""

import io
from unittest.mock import Mock

import pytest

from app import create_app
import routes.interviews as interview_routes
from services.ai.interview_service import InterviewEvaluationError
from services.backend_demo_interview_service import get_backend_demo_interview
from services.backend_demo_scenario_service import BACKEND_DEMO_COMPANY_ID


@pytest.fixture
def client():
    application = create_app(
        {"TESTING": True, "SECRET_KEY": "interview-workspace-test-key"}
    )
    with application.test_client() as test_client:
        with test_client.session_transaction() as user_session:
            user_session["user_id"] = "interview-user"
            user_session["user_email"] = "interview@example.com"
            user_session["user_name"] = "Interview User"
        yield test_client


def _interview(**overrides):
    interview = get_backend_demo_interview()
    interview.update(
        {
            "status": "in_progress",
            "career_id": "software-developer",
            "position_id": "backend-developer",
            "company_id": BACKEND_DEMO_COMPANY_ID,
            "current_question": 1,
        }
    )
    interview.update(overrides)
    return interview


def _completed_review_interview():
    interview = _interview(status="completed", current_question=5)
    interview["answers"] = {
        str(question_id): {
            "feedback": f"Feedback {question_id}",
            "filler_count": question_id,
            "hidden_answer_score": "private answer detail",
            "long_pause_count": question_id - 1,
            "question_score": 80 + question_id,
            "transcript": f"Transcript {question_id}",
            "word_count": 90 + question_id,
            "words_per_minute": 120 + question_id,
        }
        for question_id in range(1, 5)
    }
    interview["evaluation"] = {
        "areas_for_improvement": ["Use more specific examples"],
        "communication_feedback": "Clear and professional delivery.",
        "content_feedback": "Relevant answers with useful context.",
        "hidden_grading_criteria": "never expose this",
        "next_steps": ["Practice concise STAR answers"],
        "overall_score": 84.5,
        "question_results": [{"internal": "server-only duplicate"}],
        "readiness": "Stored but not shown by the legacy template.",
        "strengths": ["Structured explanations"],
        "summary": "A strong interview with clear growth opportunities.",
    }
    interview["private_rubrics"] = {"1": {"secret": "private rubric"}}
    return interview


def test_interview_review_api_has_one_exact_registered_url(client):
    review_rules = [
        rule
        for rule in client.application.url_map.iter_rules()
        if rule.endpoint == "interviews.interview_review_api"
    ]

    assert [str(rule) for rule in review_rules] == [
        "/api/interview/<interview_id>/review"
    ]
    assert review_rules[0].methods == {"GET", "HEAD", "OPTIONS"}


def test_interview_workspace_api_returns_only_browser_safe_state(client, monkeypatch):
    interview = _interview()
    interview["public_questions"][0]["accidental_private_field"] = "do not expose"
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: interview,
    )

    response = client.get("/api/interview/interview-demo")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "in_progress"
    assert payload["interview_id"] == "interview-demo"
    assert payload["current_question"] == 1
    assert len(payload["questions"]) == 4
    assert set(payload["questions"][0]) == {
        "id",
        "category",
        "question",
        "difficulty",
        "target_words",
        "time_limit_seconds",
    }
    serialized = response.get_data(as_text=True)
    assert "private_rubrics" not in serialized
    assert "accidental_private_field" not in serialized
    assert "do not expose" not in serialized


def test_interview_workspace_api_resumes_at_persisted_question(client, monkeypatch):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(current_question=3),
    )

    response = client.get("/api/interview/interview-demo")

    assert response.status_code == 200
    assert response.get_json()["current_question"] == 3


def test_completed_interview_workspace_api_points_to_existing_review(client, monkeypatch):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(status="completed"),
    )

    response = client.get("/api/interview/interview-demo")

    assert response.status_code == 200
    assert response.get_json() == {
        "interview_id": "interview-demo",
        "review_url": "/interview/interview-demo/review",
        "status": "completed",
    }


def test_interview_workspace_api_rejects_missing_attempt(client, monkeypatch):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: None,
    )

    response = client.get("/api/interview/not-owned")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Interview attempt not found."}


def test_workspace_api_recovers_a_saved_final_answer_without_exposing_report(
    client,
    monkeypatch,
):
    answers = {
        str(question_id): {"transcript": f"Answer {question_id}"}
        for question_id in range(1, 5)
    }
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(current_question=5, answers=answers),
    )
    final_evaluation = Mock(
        return_value={"overall_score": 86, "hidden_grading_detail": "private"}
    )
    complete_attempt = Mock()
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

    response = client.get("/api/interview/interview-demo")

    assert response.status_code == 200
    assert response.get_json() == {
        "interview_id": "interview-demo",
        "review_url": "/interview/interview-demo/review",
        "status": "completed",
    }
    final_evaluation.assert_called_once()
    complete_attempt.assert_called_once()
    assert "hidden_grading_detail" not in response.get_data(as_text=True)


def test_workspace_api_reports_recoverable_final_evaluation_failure(
    client,
    monkeypatch,
):
    answers = {
        str(question_id): {"transcript": f"Answer {question_id}"}
        for question_id in range(1, 5)
    }
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(current_question=5, answers=answers),
    )
    monkeypatch.setattr(
        interview_routes,
        "generate_final_interview_evaluation",
        Mock(side_effect=InterviewEvaluationError("private Gemini detail")),
    )

    response = client.get("/api/interview/interview-demo")

    assert response.status_code == 503
    message = response.get_json()["error"]
    assert "Refresh to try again" in message
    assert "private Gemini detail" not in message


def test_answer_api_rejects_duplicate_or_out_of_order_question_before_analysis(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(current_question=2),
    )
    analyze = Mock(side_effect=AssertionError("out-of-order audio was analyzed"))
    monkeypatch.setattr(interview_routes, "analyze_spoken_answer", analyze)

    response = client.post(
        "/api/interview/interview-demo/answer",
        data={
            "question_id": "1",
            "duration_seconds": "20",
            "audio": (io.BytesIO(b"duplicate audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "Please answer the current interview question."
    }
    analyze.assert_not_called()


def test_final_answer_completion_failure_returns_safe_retry_error(
    client,
    monkeypatch,
):
    interview = _interview(
        current_question=4,
        answers={
            "1": {"transcript": "Answer 1"},
            "2": {"transcript": "Answer 2"},
            "3": {"transcript": "Answer 3"},
        },
    )
    refreshed = _interview(
        current_question=5,
        answers={
            **interview["answers"],
            "4": {"transcript": "Answer 4"},
        },
    )
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        Mock(side_effect=[interview, refreshed]),
    )
    monkeypatch.setattr(
        interview_routes,
        "analyze_spoken_answer",
        Mock(return_value={"question_score": 80, "transcript": "Answer 4"}),
    )
    monkeypatch.setattr(interview_routes, "save_interview_answer", Mock())
    monkeypatch.setattr(
        interview_routes,
        "generate_final_interview_evaluation",
        Mock(return_value={"overall_score": 80}),
    )
    monkeypatch.setattr(
        interview_routes,
        "complete_interview_attempt",
        Mock(side_effect=RuntimeError("private Firebase detail")),
    )

    response = client.post(
        "/api/interview/interview-demo/answer",
        data={
            "question_id": "4",
            "duration_seconds": "45",
            "audio": (io.BytesIO(b"final audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    message = response.get_json()["error"]
    assert message == (
        "Your answers were saved, but CareerGrid could not create the final report."
    )
    assert "private Firebase detail" not in message


def test_interview_review_api_returns_only_legacy_visible_report_fields(
    client,
    monkeypatch,
):
    interview = _completed_review_interview()
    interview["public_questions"][0]["private_question_note"] = "hidden note"
    get_attempt = Mock(return_value=interview)
    monkeypatch.setattr(interview_routes, "get_interview_attempt", get_attempt)

    response = client.get("/api/interview/interview-demo/review")
    payload = response.get_json()

    assert response.status_code == 200
    assert response.is_json
    assert set(payload) == {
        "areas_for_improvement",
        "communication_feedback",
        "company_name",
        "content_feedback",
        "explore_url",
        "interview_id",
        "next_steps",
        "overall_score",
        "position_title",
        "question_results",
        "status",
        "strengths",
        "summary",
    }
    assert payload["status"] == "completed"
    assert payload["overall_score"] == 84.5
    assert payload["explore_url"] == "/career"
    assert len(payload["question_results"]) == 4
    assert set(payload["question_results"][0]) == {
        "category",
        "feedback",
        "filler_count",
        "long_pause_count",
        "question",
        "score",
        "transcript",
        "word_count",
        "words_per_minute",
    }
    assert payload["question_results"][0]["transcript"] == "Transcript 1"
    get_attempt.assert_called_once_with(
        user_id="interview-user",
        interview_id="interview-demo",
    )

    serialized = response.get_data(as_text=True)
    for private_value in [
        "never expose this",
        "private rubric",
        "private answer detail",
        "server-only duplicate",
        "Stored but not shown",
        "hidden note",
    ]:
        assert private_value not in serialized


def test_incomplete_interview_review_api_points_back_to_workspace(client, monkeypatch):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: _interview(status="in_progress"),
    )

    response = client.get("/api/interview/interview-demo/review")

    assert response.status_code == 200
    assert response.get_json() == {
        "interview_id": "interview-demo",
        "redirect_url": "/interview/interview-demo",
        "status": "in_progress",
    }


def test_unavailable_interview_review_api_preserves_career_redirect(client, monkeypatch):
    monkeypatch.setattr(
        interview_routes,
        "get_interview_attempt",
        lambda **kwargs: None,
    )

    response = client.get("/api/interview/not-owned/review")

    assert response.status_code == 200
    assert response.get_json() == {
        "redirect_url": "/career",
        "status": "unavailable",
    }
