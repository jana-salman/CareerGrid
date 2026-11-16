"""Roadmap schema, safe recovery of older reports, and learning resources.

The model is mocked; these tests follow the data from the evaluator through
normalisation, storage filtering, and the report API.
"""

import json
from unittest.mock import MagicMock, Mock

import pytest

import routes.simulations as simulation_routes
import services.ai.evaluation_service as evaluation_service
from ai_prompt.prompts.workplace_evaluation_v4 import EVALUATION_SCHEMA, build_workplace_evaluation_prompt
from app import create_app
from services.ai.roadmap import (
    RESOURCE_CATALOG,
    normalize_report_evaluation,
    normalize_review_items,
    normalize_roadmap,
    parse_literal,
    resolve_resources,
    safe_url,
)
from services.simulation.simulation_storage import get_user_visible_evaluation

REAL_ITEMS = [
    {"skill": "Edge-case testing", "evidence": "tests/test_orders.py has no case for an empty cart.",
     "gap": "Empty and duplicate inputs are untested.",
     "next_steps": ["Add a parametrized test for empty, zero, and duplicate items.", "Assert the 400 response body."]},
    {"skill": "HTTP error handling", "evidence": "orders.py returns 500 for a missing product.",
     "gap": "Clients cannot tell a bad request from a server failure.",
     "next_steps": ["Return 404 with the documented error code for unknown products."]},
]


def _no_object_text(value):
    text = json.dumps(value)
    return "{'" not in text and "'skill'" not in text and '\\"skill\\"' not in text


def test_legacy_reports_with_roadmap_objects_stored_as_text_are_recovered():
    """The reported bug: dictionaries rendered as text inside every card's numbered list."""

    as_text = [str(item) for item in REAL_ITEMS]  # Python repr, as older reports stored them
    legacy = [
        {"skill": "Technical Accuracy", "evidence": "Based on your submitted changes to orders.py: partial.",
         "gap": "Scored 5/10.", "next_steps": as_text[:2]},
        {"skill": "Communication", "evidence": "Based on your submitted changes to orders.py: brief.",
         "gap": "Scored 6/10.", "next_steps": as_text[:2]},
    ]
    roadmap = normalize_roadmap(legacy)
    assert [item["skill"] for item in roadmap] == ["Edge-case testing", "HTTP error handling"]
    assert roadmap[0]["next_steps"] == REAL_ITEMS[0]["next_steps"]
    assert roadmap[1]["evidence"] == REAL_ITEMS[1]["evidence"]
    assert all(isinstance(step, str) for item in roadmap for step in item["next_steps"])
    assert _no_object_text(roadmap)


def test_nested_step_objects_become_readable_sentences():
    roadmap = normalize_roadmap([{
        "skill": "Tracing", "evidence": "The handover does not mention the log.", "gap": "Cause not traced.",
        "next_steps": [{"step": "Follow request 42 through api.py and store.py."}, {"action": "Note each value."},
                       "{'description': 'Compare with the ticket.'}", "{broken", 7, None, ["nested", "list"]],
    }])
    # Readable steps only, at most four; truncated object text ("{broken") is dropped.
    assert roadmap[0]["next_steps"] == [
        "Follow request 42 through api.py and store.py.", "Note each value.", "Compare with the ticket.", "7",
    ]


def test_review_lists_never_show_object_text():
    items = normalize_review_items([
        "Practise authorization checks.", {"text": "Write a handover."}, str(REAL_ITEMS[0]),
        "Practise authorization checks.", {"unknown": 1},
    ])
    assert items == [
        "Practise authorization checks.", "Write a handover.",
        "Edge-case testing: Add a parametrized test for empty, zero, and duplicate items.",
    ]


def test_duplicates_are_consolidated_without_merging_different_skills():
    roadmap = normalize_roadmap([
        {"skill": "Regression tests", "evidence": "No test for the old path.", "gap": "", "next_steps": ["Add one per requirement."]},
        {"skill": "regression test", "evidence": "No test for the old path.", "gap": "Old path unprotected.",
         "next_steps": ["Add one per requirement.", "Keep the existing tests unchanged."]},
        {"skill": "Commit messages", "evidence": "Commit 'fix'.", "gap": "", "next_steps": ["Say what and why.", "Review the diff first."]},
        {"skill": "Git workflow", "evidence": "Pushed to main.", "gap": "", "next_steps": ["Review the diff first.", "Use a branch."]},
    ])
    assert [item["skill"] for item in roadmap] == ["Regression tests", "Commit messages", "Git workflow"]
    assert roadmap[0]["next_steps"] == ["Add one per requirement.", "Keep the existing tests unchanged."]
    assert roadmap[0]["gap"] == "Old path unprotected."
    # A step copied onto different skills is not specific to either.
    assert roadmap[1]["next_steps"] == ["Say what and why."] and roadmap[2]["next_steps"] == ["Use a branch."]


def test_resources_come_only_from_the_catalog_with_safe_links():
    chosen = resolve_resources([
        {"id": "pytest-parametrize", "relevance": "Covers the empty and duplicate cases you missed."},
        {"id": "made-up", "url": "https://example.com/fake"},
        {"title": "Evil", "url": "javascript:alert(1)"},
        {"url": RESOURCE_CATALOG["mdn-http-status"]["url"]},
        "owasp-input-validation",
    ])
    assert [item["id"] for item in chosen] == ["pytest-parametrize", "mdn-http-status"]
    assert chosen[0]["relevance"] == "Covers the empty and duplicate cases you missed."
    assert chosen[1]["relevance"] == RESOURCE_CATALOG["mdn-http-status"]["summary"]
    assert set(chosen[0]) == {"id", "title", "provider", "url", "relevance"}
    for url in ("javascript:alert(1)", "data:text/html,x", "https://user:pw@example.com", "https://a.b/x y", "//example.com"):
        assert safe_url(url) == ""
    assert all(safe_url(entry["url"]) == entry["url"] for entry in RESOURCE_CATALOG.values())


def test_items_without_chosen_resources_match_by_skill_or_honestly_have_none():
    roadmap = normalize_roadmap([
        {"skill": "Authorization", "evidence": "Any user can read any order.", "gap": "No ownership check.",
         "next_steps": ["Check the owner on every read."]},
        {"skill": "Stakeholder empathy", "evidence": "Reply ignored the customer.", "gap": "Tone.",
         "next_steps": ["Acknowledge the impact first."]},
    ])
    assert roadmap[0]["resources"][0]["id"] == "owasp-authorization"
    assert roadmap[1]["resources"] == []


def test_stored_text_is_parsed_as_literals_only_never_executed(monkeypatch):
    import os

    monkeypatch.setattr(os, "system", Mock(side_effect=AssertionError("executed")))
    assert parse_literal("{'skill': __import__('os').system('echo')}") is None
    assert parse_literal("[" * 5000 + "]" * 5000) is None
    assert parse_literal("{'skill': 'x', 'next_steps': ['a']}") == {"skill": "x", "next_steps": ["a"]}
    roadmap = normalize_roadmap(["{'skill': __import__('os').system('echo'), 'evidence': 'e', 'next_steps': ['a']}"])
    assert roadmap == []


def test_unrecoverable_roadmaps_are_marked_unavailable_and_scores_are_preserved():
    stored = {
        "overall_score": 64, "dimensions": {"technical_accuracy": {"score": 6, "max_score": 10, "feedback": "ok"}},
        "submission_overview": {"mode": "main", "changed_files": ["app.py"]},
        "personalized_roadmap": ["{'skill': 'Testing', 'next_steps': [", {"skill": "Only a name"}],
    }
    report = normalize_report_evaluation(stored)
    assert report["roadmap_status"] == "unavailable" and report["personalized_roadmap"] == []
    for key in ("overall_score", "dimensions", "submission_overview"):
        assert report[key] == stored[key]
    assert stored["personalized_roadmap"][1] == {"skill": "Only a name"}, "the stored record is not modified"
    assert normalize_report_evaluation({"overall_score": 50})["roadmap_status"] == "none"


def test_evaluation_schema_restricts_resources_to_catalog_ids_and_strings():
    item = EVALUATION_SCHEMA["properties"]["personalized_roadmap"]["items"]
    assert item["required"] == ["skill", "evidence", "gap", "next_steps", "resources"]
    assert item["properties"]["next_steps"]["items"] == {"type": "string"}
    assert item["properties"]["resources"]["items"]["properties"]["id"]["enum"] == sorted(RESOURCE_CATALOG)
    assert EVALUATION_SCHEMA["properties"]["recommended_next_steps"]["items"] == {"type": "string"}
    prompt = build_workplace_evaluation_prompt({"actual_user_evidence": {}})
    assert "pytest-parametrize" in prompt and "choose by id" in prompt
    assert "https://" not in prompt.split("LEARNING_RESOURCES")[1].split("Evidence:")[0], "the model never sees URLs to copy"


@pytest.fixture
def report_client(monkeypatch):
    stored = {}

    def get_attempt(**kwargs):
        return stored.get(kwargs["attempt_id"])

    monkeypatch.setattr(simulation_routes, "get_simulation_attempt", get_attempt)
    application = create_app({"TESTING": True, "SECRET_KEY": "roadmap"})
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["user_id"] = "u"
        user_session["user_email"] = "u@example.com"
    return client, stored


def test_resources_survive_evaluation_storage_and_report_loading(report_client, monkeypatch):
    client, stored = report_client
    model_output = {
        "overall_score": 72, "summary": "Solid.",
        "dimensions": {key: {"score": 7, "max_score": 10, "feedback": "f"} for key in ("technical_accuracy", "verification_testing")},
        "strengths": ["Clear commits."], "areas_for_improvement": ["Edge cases."],
        "recommended_next_steps": ["Test empty carts."],
        "personalized_roadmap": [
            {**REAL_ITEMS[0], "resources": [{"id": "pytest-parametrize", "relevance": "Shows how to cover many edge inputs."}]},
            {**REAL_ITEMS[1], "resources": [{"id": "mdn-http-status", "relevance": "Pick 404 vs 400 correctly."},
                                             {"id": "flask-errors", "relevance": "Consistent error bodies."}]},
        ],
    }
    gemini = MagicMock()
    gemini.__enter__.return_value.models.generate_content.return_value = Mock(text=json.dumps(model_output))
    monkeypatch.setattr(evaluation_service, "get_gemini_client", lambda: gemini)
    evaluation = evaluation_service.evaluate_workplace_submission({"actual_user_evidence": {
        "submission_mode": "pull_request", "changed_files": [{"path": "orders.py"}],
    }})
    config = gemini.__enter__.return_value.models.generate_content.call_args.kwargs["config"]
    assert config.response_json_schema == EVALUATION_SCHEMA

    # Storage keeps only user-visible fields; Firebase round-trips plain JSON.
    stored["a1"] = {
        "simulation_mode": "workplace", "career_id": "software-developer", "position_id": "backend-developer",
        "company_id": "technova", "public_scenario": {"task": {"subject": "Orders"}},
        "evaluation": json.loads(json.dumps(get_user_visible_evaluation(evaluation))),
    }
    report = client.get("/api/simulation/attempts/a1/report").get_json()
    roadmap = report["evaluation"]["personalized_roadmap"]
    assert report["evaluation"]["roadmap_status"] == "available"
    assert [item["skill"] for item in roadmap] == ["Edge-case testing", "HTTP error handling"]
    assert roadmap[0]["resources"] == [{
        "id": "pytest-parametrize", "title": RESOURCE_CATALOG["pytest-parametrize"]["title"],
        "provider": "pytest documentation", "url": RESOURCE_CATALOG["pytest-parametrize"]["url"],
        "relevance": "Shows how to cover many edge inputs.",
    }]
    assert [item["id"] for item in roadmap[1]["resources"]] == ["mdn-http-status", "flask-errors"]
    assert report["evaluation"]["overall_score"] == 72
    assert report["recommended_next_steps"] == ["Test empty carts."]


def test_a_legacy_report_loads_readably_through_the_api(report_client):
    client, stored = report_client
    legacy_roadmap = [
        {"skill": "Technical Accuracy", "evidence": "Based on your changes.", "gap": "Scored 5/10.",
         "next_steps": [str(REAL_ITEMS[0]), str(REAL_ITEMS[1])]},
    ]
    stored["old"] = {
        "simulation_mode": "workplace", "career_id": "software-developer", "position_id": "backend-developer",
        "company_id": "technova", "public_scenario": {"task": {"subject": "Orders"}},
        "evaluation": {"overall_score": 58, "personalized_roadmap": legacy_roadmap,
                       "recommended_next_steps": [str(REAL_ITEMS[0])], "strengths": [{"text": "Good commit"}]},
    }
    report = client.get("/api/simulation/attempts/old/report").get_json()
    assert [item["skill"] for item in report["evaluation"]["personalized_roadmap"]] == ["Edge-case testing", "HTTP error handling"]
    assert report["recommended_next_steps"] == ["Edge-case testing: Add a parametrized test for empty, zero, and duplicate items."]
    assert report["strengths"] == ["Good commit"]
    assert report["evaluation"]["overall_score"] == 58
    assert _no_object_text(report)


def test_the_deterministic_frontend_roadmap_includes_resources():
    from services.simulation.frontend_workplace_scenario_service import deterministic_frontend_scenario
    from tests.test_task_generation_consistency import _frontend_responses

    scenario = deterministic_frontend_scenario("Example", "r")
    result = evaluation_service.evaluate_frontend_workplace_progress(
        _frontend_responses("main", scenario), private_context=scenario["private_context"]
    )
    roadmap = normalize_roadmap(result["personalized_roadmap"])
    assert roadmap and all(item["resources"] for item in roadmap)
    skills = [item["skill"] for item in roadmap]
    assert len(skills) == len(set(skills))
