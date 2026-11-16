"""Generation pipeline: bounded recovery, assembly, job context, records.

The model call itself is mocked here; real-model behaviour is measured
separately with live runs (see README "Workplace Assignment Quality").
"""

import json
from copy import deepcopy
from unittest.mock import Mock

import pytest

import services.ai.generation_runtime as runtime
from ai_prompt.prompts.scenario_v5 import build_backend_prompt_v5, build_frontend_prompt_v5
from services.ai.generation_runtime import GenerationAttemptError, GenerationReport, run_generation
from services.ai.scenario_drafts import assemble_backend, assemble_frontend
from services.ai.scenario_generation_service import (
    SCENARIO_BLUEPRINTS,
    ScenarioGenerationError,
    accept_assembled,
    generate_workplace_scenario,
    validate_generated_backend_scenario,
)
from services.simulation.backend_demo_scenario_service import get_backend_demo_workplace_scenario
from services.simulation.frontend_workplace_scenario_service import generate_frontend_workplace_scenario
from services.simulation.job_context_service import build_catalog_job_context, build_job_context

BLUEPRINT = SCENARIO_BLUEPRINTS[("software-developer", "backend-developer")]


def demo_draft():
    """A model-shaped draft rebuilt from the validated TechNova assignment."""

    scenario = get_backend_demo_workplace_scenario(attempt_id="draft")
    public, private = scenario["public_scenario"], scenario["private_context"]
    task = public["task"]
    return {
        "title": public["title"], "company_name": "TechNova", "domain": "internal user profiles",
        "advisor": {"name": public["advisor"]["name"], "title": public["advisor"]["title"]},
        "email_subject": task["subject"], "email_summary": task["summary"], "email_body": task["body"],
        "requirements": task["requirements"], "acceptance_criteria": task["acceptance_criteria"],
        "deliverables": task["deliverables"], "skill_targets": public["skill_targets"],
        "project": {"display_name": public["project"]["display_name"], "slug": public["project"]["name"], "files": deepcopy(public["project"]["files"])},
        "resources": [{"name": item["name"], "content": item["content"]} for item in public["resources"]],
        "background_email": {key: public["background_emails"][0][key] for key in ("sender_name", "sender_title", "subject", "body")},
        "private": {
            "root_cause": private["root_cause"],
            "expected_changes": private["expected_changes"],
            "acceptable_alternatives": private["acceptable_alternatives"],
            "verification_expectations": private["verification_expectations"],
            "hints": [item["guidance"] for item in private["progressive_guidance"]],
            "assessment_criteria": [
                {"id": item["id"], "criterion": item["criterion"], "evidence": item["evidence"], "files": item["files"], "requirement_numbers": item["requirement_refs"]}
                for item in private["assessment_criteria"]
            ],
            "starter_gap_checks": [
                {"id": check["id"], "file": check["any_of"][0]["file"], "must_include_any": check["any_of"][0]["must_include_any"]}
                for check in private["starter_gap_checks"]
            ],
            "important_evidence": private["evaluation_notes"]["important_evidence"],
        },
    }


@pytest.fixture
def fast_budget(monkeypatch):
    monkeypatch.setenv("SCENARIO_GENERATION_BUDGET_SECONDS", "120")
    monkeypatch.setenv("SCENARIO_GENERATION_MAX_ATTEMPTS", "3")


def test_a_model_shaped_draft_assembles_into_a_scenario_that_passes_every_gate():
    scenario, repairs = assemble_backend(demo_draft(), attempt_id="a1", difficulty="junior")
    validated = validate_generated_backend_scenario(scenario)
    task = validated["public_scenario"]["task"]
    assert task["attachments"] == [item["id"] for item in validated["public_scenario"]["resources"]]
    assert validated["public_scenario"]["advisor"]["email"].endswith("@technova.example")
    assert len(validated["private_context"]["progressive_guidance"]) == 3
    assert repairs == []


def test_only_provably_false_details_are_repaired():
    draft = demo_draft()
    draft["resources"][0]["content"] += "\nTraceback at serializers.py:999\n"
    scenario, repairs = assemble_backend(draft, attempt_id="a2", difficulty="junior")
    assert "serializers.py:999" not in scenario["public_scenario"]["resources"][0]["content"]
    assert repairs == []
    validate_generated_backend_scenario(scenario)


def test_rubric_gaps_are_rejected_not_silently_repaired():
    """Missing criterion files and gap checks the starter already passes are
    kept and rejected with specific feedback, never dropped."""

    draft = demo_draft()
    draft["private"]["assessment_criteria"][0]["files"].append("does/not/exist.py")
    draft["private"]["starter_gap_checks"].append({"id": "already", "file": "api/profiles.py", "must_include_any": ["Blueprint"]})
    scenario, repairs = assemble_backend(draft, attempt_id="a3", difficulty="junior")
    assert "already" in [check["id"] for check in scenario["private_context"]["starter_gap_checks"]]
    assert any("does/not/exist.py" in item for item in repairs if item.startswith("defect: "))
    with pytest.raises(GenerationAttemptError) as rejected:
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)
    feedback = " ".join(rejected.value.feedback)
    assert "already satisfies 'already'" in feedback and "api/profiles.py already contains one of ['Blueprint']" in feedback
    assert "does/not/exist.py" in feedback


def test_a_new_test_file_may_be_named_by_a_criterion():
    draft = demo_draft()
    draft["private"]["assessment_criteria"][0]["files"].append("tests/test_new_behaviour.py")
    scenario, repairs = assemble_backend(draft, attempt_id="a4", difficulty="junior")
    assert repairs == []
    assert "tests/test_new_behaviour.py" in scenario["private_context"]["assessment_criteria"][0]["files"]


def test_frontend_assembly_builds_the_fixed_workflow_structure():
    draft = {
        "title": "Filters", "company_name": "x", "domain": "store", "advisor": {"name": "Ana Silva", "title": "Lead"},
        "email_subject": "s", "email_summary": "s", "email_body": "b", "requirements": [], "acceptance_criteria": [],
        "deliverables": [], "skill_targets": [], "issue_id": "fe 42!",
        "project": {"display_name": "Store", "slug": "Store App", "files": [{"path": "index.html", "content": "<p>"}, {"path": "tests/a.test.js", "content": "t"}]},
        "resources": [{"name": "qa notes.md", "content": "n"}],
        "critical_email": {"sender_name": "Ana Silva", "sender_title": "Lead", "subject": "Filters broken", "body": "Help"},
        "other_emails": [{"sender_name": f"P{i}", "sender_title": "T", "subject": f"S{i}", "body": "B", "priority": "low"} for i in range(6)],
        "private": {"root_cause": "r", "root_cause_keywords": ["Filter"], "expected_changes": [{"file": "js/app.js", "change": "c"}],
                    "acceptable_alternatives": [], "verification_expectations": [],
                    "patch_checks": [{"id": "Has Filter", "category": "weird", "description": "d", "feedback": "f", "file": "index.html", "must_include_any": ["<ul"], "must_not_include": []},
                                     {"id": "gone", "category": "correctness", "description": "d", "feedback": "f", "file": "missing.js", "must_include_any": ["x"], "must_not_include": []}]},
    }
    scenario, repairs = assemble_frontend(draft, attempt_id="f1", company_name="PixelWorks")
    public, private = scenario["public_scenario"], scenario["private_context"]
    assert [task["application"] for task in public["frontend_tasks"]] == ["mail", "browser", "vscode", "testing", "github"]
    assert len(public["inbox_emails"]) == 5 and public["inbox_emails"][0]["priority"] == "critical"
    assert public["inbox_emails"][0]["linked_ticket_id"] == public["issue_id"] == "FE42"
    assert public["project"]["name"] == "store-app"
    assert '"test": "node --test"' in next(f for f in public["project"]["files"] if f["path"] == "package.json")["content"]
    assert [check["id"] for check in private["patch_checks"]] == ["has_filter", "gone"]
    assert private["patch_checks"][0]["category"] == "correctness"
    assert set(private["expected_patch"]) == {"js_app_js"}
    assert "defect: patch check 'gone' targets missing.js, which is not in the project." in repairs


def test_quota_errors_stop_immediately_and_are_recorded(monkeypatch, fast_budget):
    calls = Mock(side_effect=Exception("429 RESOURCE_EXHAUSTED quota exceeded key=AIzaSECRETSECRETSECRET"))
    monkeypatch.setattr(runtime, "call_model_json", calls)
    report = GenerationReport()
    assert run_generation(report=report, build_prompt=lambda feedback: "p", build_scenario=lambda draft: draft, schema=None, temperature=0.5) is None
    assert calls.call_count == 1
    assert report.outcome == "fallback" and report.failure_reason == "quota_exhausted"
    assert "AIza" not in json.dumps(report.to_record()) and "SECRET" not in json.dumps(report.to_record())


def test_rejections_feed_back_into_the_next_attempt(monkeypatch, fast_budget):
    prompts = []
    monkeypatch.setattr(runtime, "call_model_json", lambda prompt, **kwargs: {"draft": len(prompts)})

    def build_prompt(feedback):
        prompts.append(feedback)
        return "p"

    def build_scenario(draft):
        if draft["draft"] < 3:
            raise GenerationAttemptError("quality", "thin", ["README section 'Overview' is too thin to be useful."])
        return {"ok": True}

    report = GenerationReport()
    assert run_generation(report=report, build_prompt=build_prompt, build_scenario=build_scenario, schema=None, temperature=0.5) == {"ok": True}
    assert prompts[0] is None and "too thin" in prompts[1][0]
    assert [item["outcome"] for item in report.attempts] == ["rejected", "rejected", "accepted"]
    assert report.outcome == "generated"


def test_the_time_budget_bounds_waiting(monkeypatch, fast_budget):
    clock = iter([0, 0, 100, 100, 200, 200, 300])
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(runtime, "call_model_json", Mock(side_effect=Exception("Read timed out")))
    report = GenerationReport()
    report.started = 0
    assert run_generation(report=report, build_prompt=lambda f: "p", build_scenario=lambda d: d, schema=None, temperature=0.5) is None
    assert report.failure_reason == "time_budget_exhausted"
    assert [item["reason"] for item in report.attempts] == ["timeout"]


def test_generator_raises_for_fallback_and_reports_why(monkeypatch, fast_budget):
    monkeypatch.setattr(runtime, "call_model_json", Mock(side_effect=Exception("404 NOT_FOUND model")))
    report = GenerationReport()
    with pytest.raises(ScenarioGenerationError):
        generate_workplace_scenario(career_id="software-developer", position_id="backend-developer", company_id="x", attempt_id="z", report=report)
    assert report.failure_reason == "model_unavailable" and report.kind == "backend"

    frontend_report = GenerationReport()
    scenario, count = generate_frontend_workplace_scenario(company_name="PixelWorks", attempt_id="z", report=frontend_report)
    assert count == 0 and scenario["public_scenario"]["scenario_kind"] == "frontend_workplace"
    assert frontend_report.outcome == "fallback"


def test_prompts_carry_job_context_honestly_without_rotation():
    excerpt = build_job_context("adzuna", {"title": "Backend Developer", "company": "Acme", "description": "Build PostgreSQL APIs for a real-time platform…"})
    assert excerpt["excerpt"] is True
    prompt = build_backend_prompt_v5(role="Backend Developer", difficulty="junior", competencies=["APIs"], job_context=excerpt)
    assert "Build PostgreSQL APIs for a real-time platform" in prompt
    assert "SHORT EXCERPT" in prompt and "Do not invent further employer-specific requirements" in prompt
    assert "untrusted external data" in prompt
    # One saved assignment per role: no per-attempt type rotation or "be different" history.
    for removed in ("meaningfully different", "ASSIGNMENT TYPE for this attempt", "recently received"):
        assert removed not in prompt
    flat = " ".join(prompt.split())
    assert "feature request or the investigation" in flat and "30-60 minutes" in flat

    catalog = build_catalog_job_context("frontend-developer", "cloudbyte")
    frontend = build_frontend_prompt_v5(company_name="CloudByte", job_context=catalog)
    assert "cloud dashboard for small businesses" in frontend and "fictional practice company" in frontend
    assert build_catalog_job_context("backend-developer", "unknown") is None


def test_start_route_passes_the_listing_description_and_records_generation(monkeypatch):
    import routes.simulations as simulation_routes
    from app import create_app

    saved = {}
    prompts = []
    monkeypatch.setenv("SCENARIO_GENERATION_BUDGET_SECONDS", "120")
    monkeypatch.setattr(simulation_routes, "create_workplace_simulation_attempt", lambda **kwargs: "attempt-live")
    monkeypatch.setattr(simulation_routes, "save_workplace_scenario", lambda **kwargs: saved.update(kwargs))

    def fake_model(prompt, **kwargs):
        prompts.append(prompt)
        raise Exception("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(runtime, "call_model_json", fake_model)
    client = create_app({"TESTING": True, "SECRET_KEY": "k"}).test_client()
    with client.session_transaction() as user_session:
        user_session["user_id"] = "u"
        user_session["user_email"] = "u@example.com"
    response = client.post("/api/simulation/workplace/start", json={
        "career_id": "software-developer", "position_id": "backend-developer", "company_id": "Acme",
        "job_source": "adzuna", "client_request_id": "aaaaaaaa-1111",
        "job_context": {"title": "Backend Developer", "company": "Acme", "description": "Maintain payment reconciliation services in Python…"},
    })
    assert response.status_code == 201
    assert "Maintain payment reconciliation services in Python" in prompts[0]
    assert saved["generation_source"] == "fallback"
    details = saved["generation_details"]
    assert details["outcome"] == "fallback" and details["failure_reason"] == "quota_exhausted"
    assert details["job_context_source"] == "adzuna" and details["prompt_version"] == "scenario_v5_shared"
    assert details["pipeline"] == "single" and details["failure_category"] == "availability"
    assert details["attempts"][0]["stage"] == "draft"
    assert "generation" not in json.dumps(response.get_json())


def test_readme_is_composed_from_model_content_and_server_facts():
    draft = demo_draft()
    draft["readme"] = {
        "overview": "Overview text. " * 20,
        "file_responsibilities": [{"path": "api/profiles.py", "responsibility": "HTTP routes and query validation."}],
        "expected_behaviour": "Behaviour text. " * 25,
        "example": "GET /api/users/101 -> 200",
        "sample_data_and_resources": "Data text. " * 20,
        "verification_notes": "Trace the lookup path and compare with users.json. " * 4,
        "test_command": "pytest",
    }
    scenario, repairs = assemble_backend(draft, attempt_id="r1", difficulty="junior")
    readme = next(item["content"] for item in scenario["public_scenario"]["project"]["files"] if item["path"] == "README.md")
    assert "composed_readme" in repairs
    assert "- `api/profiles.py` - HTTP routes and query validation." in readme
    assert "- `services/user_service.py` - (not described)" in readme
    assert "defect: README file_responsibilities must describe services/user_service.py." in repairs
    assert "```text\nGET /api/users/101 -> 200\n```" in readme
    assert "CareerGrid's terminal cannot run code or tests" in readme
    for deliverable in scenario["public_scenario"]["task"]["deliverables"]:
        assert f"- {deliverable}" in readme
    with pytest.raises(GenerationAttemptError, match="must describe"):
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_uncovered_requirements_are_rejected_not_given_invented_criteria():
    draft = demo_draft()
    for item in draft["private"]["assessment_criteria"]:
        item["requirement_numbers"] = [1]
    scenario, repairs = assemble_backend(draft, attempt_id="c1", difficulty="junior")
    refs = {ref for item in scenario["private_context"]["assessment_criteria"] for ref in item["requirement_refs"]}
    assert refs == {1}
    with pytest.raises(ScenarioGenerationError, match=r"Requirements \[2, 3, 4\] are not covered"):
        validate_generated_backend_scenario(scenario)


def test_schema_bounds_list_sizes_that_used_to_cause_rejections():
    from services.ai.scenario_drafts import BACKEND_DRAFT_SCHEMA, FRONTEND_DRAFT_SCHEMA

    private = BACKEND_DRAFT_SCHEMA["properties"]["private"]["properties"]
    requirement = BACKEND_DRAFT_SCHEMA["properties"]["requirements"]
    # Each requirement carries its kind and its own assessment.
    assert (requirement["minItems"], requirement["maxItems"]) == (3, 5)
    assert {"requirement", "kind", "criterion", "evidence", "files"} <= set(requirement["items"]["properties"])
    assert "assessment_criteria" not in private
    assert private["starter_gap_checks"]["minItems"] == 2
    frontend_private = FRONTEND_DRAFT_SCHEMA["properties"]["private"]["properties"]
    assert (frontend_private["patch_checks"]["minItems"], frontend_private["patch_checks"]["maxItems"]) == (4, 8)
    assert FRONTEND_DRAFT_SCHEMA["properties"]["other_emails"]["minItems"] == 4
    # minLength is accepted but not enforced by Gemini; the quality gate checks length.
    assert BACKEND_DRAFT_SCHEMA["properties"]["readme"]["properties"]["overview"]["minLength"] == 250


def test_overloaded_model_errors_are_retried_with_backoff(monkeypatch, fast_budget):
    sleeps = []
    monkeypatch.setattr(runtime.time, "sleep", lambda seconds: sleeps.append(seconds))
    responses = iter([Exception("503 UNAVAILABLE high demand"), {"draft": 1}])

    def fake_call(prompt, **kwargs):
        item = next(responses)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(runtime, "call_model_json", fake_call)
    report = GenerationReport()
    assert run_generation(report=report, build_prompt=lambda f: "p", build_scenario=lambda d: d, schema=None, temperature=0.5) == {"draft": 1}
    assert report.attempts[0]["reason"] == "model_overloaded" and sleeps and sleeps[0] > 0


def test_domain_nouns_that_are_class_names_are_not_treated_as_code_leaks():
    scenario = deepcopy(get_backend_demo_workplace_scenario(attempt_id="n"))
    services = next(f for f in scenario["public_scenario"]["project"]["files"] if f["path"] == "services/user_service.py")
    services["content"] += "\n\nclass Ticket:\n    pass\n"
    scenario["public_scenario"]["task"]["requirements"][0] += " Each Ticket reference stays unchanged."
    from services.ai.scenario_quality import assignment_quality_problems
    assert not any("observable behaviour" in problem for problem in assignment_quality_problems(scenario, kind="backend"))


def test_overloads_do_not_use_up_quality_attempts(monkeypatch, fast_budget):
    monkeypatch.setattr(runtime.time, "sleep", lambda seconds: None)
    monkeypatch.setenv("SCENARIO_GENERATION_MAX_ATTEMPTS", "2")
    responses = iter([Exception("503 UNAVAILABLE"), Exception("503 UNAVAILABLE"), {"n": 1}, {"n": 2}])

    def fake_call(prompt, **kwargs):
        item = next(responses)
        if isinstance(item, Exception):
            raise item
        return item

    def build(draft):
        if draft["n"] == 1:
            raise GenerationAttemptError("quality", "thin", ["thin"])
        return draft

    monkeypatch.setattr(runtime, "call_model_json", fake_call)
    report = GenerationReport()
    assert run_generation(report=report, build_prompt=lambda f: "p", build_scenario=build, schema=None, temperature=0.5) == {"n": 2}
    assert [item["reason"] for item in report.attempts] == ["model_overloaded", "model_overloaded", "quality", ""]


def test_tickets_may_mention_bugs_but_code_comments_may_not_point_at_them():
    scenario = deepcopy(get_backend_demo_workplace_scenario(attempt_id="l"))
    scenario["public_scenario"]["resources"][1]["content"] = "# Bug report SUP-2291\nThis is a known issue for support.\n" + scenario["public_scenario"]["resources"][1]["content"]
    validate_generated_backend_scenario(scenario)
    for comment in ("# BUG: wrong total", "# FIXME", "# TODO: fix lookup"):
        leaked = deepcopy(scenario)
        target = next(f for f in leaked["public_scenario"]["project"]["files"] if f["path"] == "services/user_service.py")
        target["content"] = f"{comment}\n" + target["content"]
        with pytest.raises(ScenarioGenerationError, match="reveals the solution"):
            validate_generated_backend_scenario(leaked)
