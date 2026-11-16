"""Staged generation (spec, then build) and the candidate archive.

The model call is mocked; these tests prove the plumbing: the spec is checked
before the build, the build is held to its plan, nothing is invented to make
a draft pass, and every candidate is preserved with its reasons. Live
behaviour is measured separately (scripts/compare_generation_models.py).
"""

import json
from copy import deepcopy

import pytest

import services.ai.generation_runtime as runtime
from services.ai.generation_runtime import GenerationReport, failure_category
from services.ai.scenario_drafts import merge_spec_and_build, spec_problems
from services.ai.scenario_generation_service import generate_workplace_scenario
from services.ai.scenario_quality import is_test_file
from tests.test_generation_pipeline import demo_draft

README_FIELDS = {
    "overview": "The profile service answers lookups from the internal support tools and the account pages. " * 3,
    "expected_behaviour": "A lookup by numeric id returns the active profile with its availability; unknown ids return a 404 error body. " * 3,
    "example": "GET /api/users/101 -> 200 {\"id\": 101, \"availability\": \"available\"}",
    "sample_data_and_resources": "The users.json fixture holds the sample profiles, and the evidence files show what support observed in production. " * 2,
    "verification_notes": "Trace the lookup path from the route through the service and serializer and compare it with the fixture data. " * 2,
}


def split_demo():
    """Turn the validated TechNova draft into a matching (spec, build) pair."""

    draft = demo_draft()
    files = [item for item in draft["project"]["files"] if item["path"] != "README.md"]
    private = draft["private"]
    spec = {
        **{key: deepcopy(draft[key]) for key in ("title", "company_name", "domain", "advisor", "requirements",
                                                  "acceptance_criteria", "deliverables", "skill_targets")},
        "product_overview": "An internal user profile service used by support and account pages.",
        "situation": "Support reports that profile availability is wrong for some users.",
        "project": {"display_name": draft["project"]["display_name"], "slug": draft["project"]["slug"]},
        "files": [
            {
                "path": item["path"],
                "role": "test" if is_test_file(item["path"]) else "source",
                "responsibility": f"Owns the {item['path']} part of the profile service.",
                "existing_behaviour": "Already serves the existing profile lookups correctly for active users.",
            }
            for item in files
        ],
        "evidence": [{"name": item["name"], "shows": "What support observed."} for item in draft["resources"]],
        "root_cause": private["root_cause"],
        "expected_changes": [{"path": item["path"], "change": item["expectation"]} for item in private["expected_changes"]],
        "test_command": "pytest",
    }
    build = {
        "files": deepcopy(files),
        "readme": dict(README_FIELDS),
        "resources": deepcopy(draft["resources"]),
        "email_subject": draft["email_subject"],
        "email_summary": draft["email_summary"],
        "email_body": draft["email_body"],
        "background_email": deepcopy(draft["background_email"]),
        "private": {key: deepcopy(value) for key, value in private.items() if key not in {"root_cause", "expected_changes"}},
    }
    return spec, build


@pytest.fixture
def staged(monkeypatch, tmp_path):
    monkeypatch.setenv("SCENARIO_GENERATION_PIPELINE", "staged")
    monkeypatch.setenv("SCENARIO_GENERATION_BUDGET_SECONDS", "120")
    monkeypatch.setenv("SCENARIO_CANDIDATE_ARCHIVE", "1")
    monkeypatch.setenv("SCENARIO_CANDIDATE_DIR", str(tmp_path))
    return tmp_path


def fake_model(monkeypatch, responses):
    prompts = []

    def call(prompt, **kwargs):
        prompts.append(prompt)
        return deepcopy(responses.pop(0))

    monkeypatch.setattr(runtime, "call_model_json", call)
    return prompts


def generate(report):
    return generate_workplace_scenario(
        career_id="software-developer", position_id="backend-developer", company_id="brightsoft",
        attempt_id="attempt-1", report=report,
    )


def archived(root):
    return {path.name: json.loads(path.read_text(encoding="utf-8")) for path in root.rglob("*.json")}


def test_a_matching_spec_and_build_pass_every_gate_and_are_archived(monkeypatch, staged):
    spec, build = split_demo()
    assert spec_problems(spec, kind="backend") == []
    prompts = fake_model(monkeypatch, [spec, build])
    report = GenerationReport()
    scenario, _ = generate(report)
    assert scenario["public_scenario"]["title"] == spec["title"]
    assert [item["stage"] for item in report.attempts] == ["spec", "build"]
    assert report.pipeline == "staged" and report.outcome == "generated" and report.api_calls == 2
    assert spec["title"] in prompts[1] and "<task_specification>" in prompts[1]
    files = archived(staged)
    assert set(files) == {"01-spec-accepted.json", "02-build-accepted.json", "summary.json"}
    assert files["02-build-accepted.json"]["output"]["public_scenario"]["title"] == spec["title"]
    assert files["summary.json"]["outcome"] == "generated"


def test_a_weak_spec_is_corrected_before_any_code_is_written(monkeypatch, staged):
    spec, build = split_demo()
    weak = deepcopy(spec)
    weak["files"] = [item for item in weak["files"] if not is_test_file(item["path"])]
    weak["requirements"][0] += " Change services/user_service.py to do it."
    problems = spec_problems(weak, kind="backend")
    assert any("existing test file" in problem for problem in problems)
    assert not any("naming" in problem for problem in problems)  # naming files is allowed
    prompts = fake_model(monkeypatch, [weak, spec, build])
    report = GenerationReport()
    generate(report)
    assert [(item["stage"], item["outcome"]) for item in report.attempts] == [
        ("spec", "rejected"), ("spec", "accepted"), ("build", "accepted"),
    ]
    assert "YOUR PREVIOUS DRAFT WAS REJECTED" in prompts[1] and "existing test file" in prompts[1]
    rejected = archived(staged)["01-spec-rejected.json"]
    assert rejected["draft"] == weak and rejected["problems"] == problems


def test_a_build_that_drops_planned_work_is_rejected_and_retried_on_the_same_spec(monkeypatch, staged):
    spec, build = split_demo()
    partial = deepcopy(build)
    dropped = partial["files"].pop()["path"]
    partial["resources"].pop()
    prompts = fake_model(monkeypatch, [spec, partial, build])
    report = GenerationReport()
    generate(report)
    assert [(item["stage"], item["outcome"]) for item in report.attempts] == [
        ("spec", "accepted"), ("build", "rejected"), ("build", "accepted"),
    ]
    assert f"missing: {dropped}" in prompts[2]
    rejected = archived(staged)["02-build-rejected.json"]
    assert rejected["draft"] == partial
    assert any("planned evidence file" in problem for problem in rejected["problems"])


def test_merge_never_fills_in_missing_material():
    spec, build = split_demo()
    build["files"] = build["files"][:2]
    draft, defects = merge_spec_and_build(spec, build, kind="backend")
    assert len(draft["project"]["files"]) == 2
    assert defects and defects[0].startswith("defect: Write every planned file")


def test_failures_are_categorised_as_api_availability_or_draft_quality():
    for reason in ("quota_exhausted", "timeout", "model_overloaded", "model_unavailable", "time_budget_exhausted"):
        assert failure_category(reason) == "availability"
    for reason in ("quality", "spec_quality", "structure", "solution_leak", "invalid_json"):
        assert failure_category(reason) == "quality"
    assert failure_category("") == ""


def test_api_errors_are_archived_with_redacted_details(monkeypatch, staged):
    def call(prompt, **kwargs):
        raise Exception("429 RESOURCE_EXHAUSTED key=AIzaSECRETSECRETSECRET")

    monkeypatch.setattr(runtime, "call_model_json", call)
    report = GenerationReport()
    with pytest.raises(Exception):
        generate(report)
    files = archived(staged)
    assert files["01-spec-error.json"]["reason"] == "quota_exhausted"
    assert "SECRET" not in json.dumps(files)
    assert files["summary.json"]["failure_category"] == "availability"


def test_the_single_call_pipeline_remains_selectable(monkeypatch, staged):
    monkeypatch.setenv("SCENARIO_GENERATION_PIPELINE", "single")
    draft = demo_draft()
    for item in draft["project"]["files"]:
        if item["path"] == "README.md":
            draft["project"]["files"].remove(item)
            break
    spec, _ = split_demo()
    draft["readme"] = {**README_FIELDS, "file_responsibilities": [
        {"path": item["path"], "responsibility": item["responsibility"]} for item in spec["files"]
    ], "test_command": "pytest"}
    fake_model(monkeypatch, [draft])
    report = GenerationReport()
    generate(report)
    assert report.pipeline == "single" and report.prompt_version == "scenario_v5_shared"
    assert [item["stage"] for item in report.attempts] == ["draft"]


# --- Rules corrected from inspected live rejections (2026-11-16) ------------


def test_real_edge_case_wording_is_recognised():
    """A live spec was rejected although it covered non-existent IDs and other users' records."""

    spec, _ = split_demo()
    spec["requirements"] = [
        "Return a 403 Forbidden error if a user attempts to access an enrollment record that does not belong to them.",
        "Ensure that valid requests for a user's own enrollment record still return the full data with a 200 OK status.",
        "Handle requests for non-existent enrollment IDs by returning a 404 Not Found status.",
    ]
    spec["acceptance_criteria"] = ["The owner receives a 200 status code."]
    assert not any("edge cases" in problem for problem in spec_problems(spec, kind="backend"))


def test_package_imports_count_as_connections():
    from services.ai.scenario_quality import project_edges

    files = {
        "app/routes/shipments.py": "from app.services import shipment_service\n",
        "app/services/shipment_service.py": "from app.utils.pagination import apply_pagination\nfrom . import helpers\n",
        "app/services/helpers.py": "def x():\n    return 1\n",
        "app/utils/pagination.py": "def apply_pagination(items, limit, offset):\n    return items\n",
    }
    assert project_edges(files) == {
        ("app/routes/shipments.py", "app/services/shipment_service.py"),
        ("app/services/shipment_service.py", "app/utils/pagination.py"),
        ("app/services/shipment_service.py", "app/services/helpers.py"),
    }


@pytest.mark.parametrize("comment", [
    "# Should check if 15 <= duration <= 120",
    "    # The total_count should reflect the filtered set size",
    "# Note: Current behavior returns 500, requirement asks for 400",
    "# BUG: Off-by-one error in capacity check",
    "// should validate the quantity before adding",
])
def test_hint_comments_from_live_drafts_are_rejected_with_the_line(comment):
    from services.ai.scenario_generation_service import ScenarioGenerationError, validate_generated_backend_scenario
    from services.simulation.backend_demo_scenario_service import get_backend_demo_workplace_scenario

    scenario = deepcopy(get_backend_demo_workplace_scenario(attempt_id="h"))
    target = next(f for f in scenario["public_scenario"]["project"]["files"] if f["path"] == "services/user_service.py")
    target["content"] = comment.replace("//", "#") + "\n" + target["content"]
    with pytest.raises(ScenarioGenerationError, match="reveals the solution in services/user_service.py"):
        validate_generated_backend_scenario(scenario)


def test_ordinary_code_comments_are_still_allowed():
    from services.ai.scenario_generation_service import CODE_COMMENT_LEAK_PATTERN

    for comment in ("# Load shipments from the JSON fixture", "# Callers should pass a list of ids",
                    "// Render each product card", "# Behaviour shared by the export and API paths"):
        assert not CODE_COMMENT_LEAK_PATTERN.search(comment), comment


def test_a_title_that_only_names_the_role_is_rejected():
    from services.ai.scenario_quality import assignment_quality_problems
    from services.simulation.backend_demo_scenario_service import get_backend_demo_workplace_scenario

    scenario = deepcopy(get_backend_demo_workplace_scenario(attempt_id="t"))
    assert not any("title" in problem for problem in assignment_quality_problems(scenario, kind="backend"))
    for title in ("Junior Backend Developer", "Backend Developer"):
        scenario["public_scenario"]["title"] = title
        assert any("name the work" in problem for problem in assignment_quality_problems(scenario, kind="backend"))


def test_staged_backend_builds_assess_every_requirement_by_schema():
    from services.ai.scenario_drafts import build_schema_for

    spec, build = split_demo()
    schema = build_schema_for(spec, "backend")
    assessments = schema["properties"]["private"]["properties"]["requirement_assessments"]
    assert assessments["minItems"] == assessments["maxItems"] == len(spec["requirements"])
    assert "assessment_criteria" not in schema["properties"]["private"]["properties"]

    build["private"].pop("assessment_criteria")
    build["private"]["requirement_assessments"] = [
        {"criterion": f"Requirement {n} is met.", "evidence": "Code and tests.", "files": ["services/user_service.py"]}
        for n in range(1, len(spec["requirements"]) + 1)
    ]
    # An unrequested extra criterion is ignored: only public requirements are assessed.
    build["private"]["additional_criteria"] = [{"criterion": "Handover is clear.", "evidence": "Reply.", "files": ["services/user_service.py"]}]
    assert "additional_criteria" not in schema["properties"]["private"]["properties"]
    draft, defects = merge_spec_and_build(spec, build, kind="backend")
    criteria = draft["private"]["assessment_criteria"]
    assert defects == []
    assert [item["requirement_numbers"] for item in criteria] == [[n] for n in range(1, len(spec["requirements"]) + 1)]
