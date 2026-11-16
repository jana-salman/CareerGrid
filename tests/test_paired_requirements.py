"""Single-pipeline drafts pair each requirement with its assessment.

Built from the validated TechNova assignment reshaped into the paired schema,
so these tests exercise the real assembly, validators, and quality gate.
"""

from copy import deepcopy

import pytest

from services.ai.generation_runtime import GenerationAttemptError
from services.ai.scenario_drafts import assemble_backend
from services.ai.scenario_generation_service import (
    ScenarioGenerationError,
    accept_assembled,
    validate_generated_backend_scenario,
)
from services.ai.scenario_quality import assignment_quality_problems
from tests.test_staged_generation import README_FIELDS, split_demo
from tests.test_generation_pipeline import demo_draft


def paired_draft():
    draft = demo_draft()
    spec, _ = split_demo()
    criteria = {ref: item for item in draft["private"].pop("assessment_criteria") for ref in item["requirement_numbers"]}
    kinds = ["behaviour", "edge_case", "edge_case", "preserve"]
    draft["requirements"] = [
        {"requirement": text, "kind": kinds[min(index, 3)] if index < len(draft["requirements"]) - 1 else "preserve",
         "criterion": criteria[index + 1]["criterion"], "evidence": criteria[index + 1]["evidence"],
         "files": criteria[index + 1]["files"]}
        for index, text in enumerate(draft["requirements"])
    ]
    draft["private"]["additional_criteria"] = []
    draft["project"]["files"] = [item for item in draft["project"]["files"] if item["path"] != "README.md"]
    draft["readme"] = {**README_FIELDS, "file_responsibilities": [
        {"path": item["path"], "responsibility": item["responsibility"]} for item in spec["files"]
    ], "test_command": "pytest"}
    return draft


def test_a_paired_draft_passes_every_gate_with_one_criterion_per_requirement():
    draft = paired_draft()
    scenario, repairs = assemble_backend(draft, attempt_id="p1", difficulty="junior")
    validated = accept_assembled(scenario, repairs, validate_generated_backend_scenario)
    private = validated["private_context"]
    assert [item["requirement_refs"] for item in private["assessment_criteria"]] == [[n] for n in range(1, len(draft["requirements"]) + 1)]
    assert private["requirement_kinds"][-1] == "preserve"
    assert validated["public_scenario"]["task"]["requirements"] == [item["requirement"] for item in draft["requirements"]]


def test_declared_kinds_satisfy_edge_case_and_preserve_without_keywords():
    draft = paired_draft()
    draft["requirements"][1]["requirement"] = "Profiles whose account was merged return the surviving profile id."
    draft["requirements"][-1]["requirement"] = "Lookups by email return the same profile body as today."
    draft["acceptance_criteria"] = ["The merged-account case and email lookups behave as described."] * 3
    scenario, _ = assemble_backend(draft, attempt_id="p2", difficulty="junior")
    problems = assignment_quality_problems(scenario, kind="backend")
    assert not any("edge cases" in problem or "preserved" in problem for problem in problems)


def test_pr_description_wording_is_neutralised_and_pr_only_delivery_is_rejected():
    draft = paired_draft()
    draft["deliverables"][0] = "A pull request description explaining the root cause and the fix."
    scenario, repairs = assemble_backend(draft, attempt_id="p3", difficulty="junior")
    assert "pr_description_to_handover_reply" in repairs
    assert scenario["public_scenario"]["task"]["deliverables"][0] == "A handover reply explaining the root cause and the fix."
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)

    required = paired_draft()
    required["deliverables"][0] = "You must open a pull request against main."
    scenario, repairs = assemble_backend(required, attempt_id="p4", difficulty="junior")
    with pytest.raises(GenerationAttemptError, match="Do not require a pull request"):
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)

    optional = paired_draft()
    optional["deliverables"][0] = "You should open a pull request or push directly to main, then reply to the email."
    scenario, repairs = assemble_backend(optional, attempt_id="p5", difficulty="junior")
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_a_role_only_title_uses_the_models_own_email_subject():
    draft = paired_draft()
    draft["title"] = "Junior Backend Developer"
    scenario, repairs = assemble_backend(draft, attempt_id="p6", difficulty="junior")
    assert scenario["public_scenario"]["title"] == draft["email_subject"]
    assert "title_from_email_subject" in repairs


@pytest.mark.parametrize("text", [
    "Can you fix it before Friday's release?",
    "We still don't know what the root cause is.",
    "The root cause is unknown at this point.",
    "Customers saw an incorrect value on the invoice page.",
])
def test_ordinary_ticket_language_is_not_a_solution_leak(text):
    draft = paired_draft()
    draft["email_body"] += f"\n\n{text}"
    scenario, repairs = assemble_backend(draft, attempt_id="p7", difficulty="junior")
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)


@pytest.mark.parametrize("text", [
    "The root cause is the cache key ignoring the tenant id.",
    "The fix is to compare normalised emails.",
])
def test_stating_the_cause_or_fix_is_still_a_leak(text):
    draft = paired_draft()
    draft["email_body"] += f"\n\n{text}"
    scenario, repairs = assemble_backend(draft, attempt_id="p8", difficulty="junior")
    with pytest.raises(GenerationAttemptError, match="reveals the solution"):
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_library_frames_in_a_traceback_are_allowed_but_project_lines_are_checked():
    draft = paired_draft()
    draft["resources"][0]["content"] += (
        "\n  File \"/usr/lib/python3.12/site-packages/flask/app.py:1498\", in full_dispatch_request\n"
    )
    scenario, repairs = assemble_backend(draft, attempt_id="p9", difficulty="junior")
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_a_new_regression_test_file_counts_as_a_planned_change():
    """Live draft 1 (2026-11-16) planned tests/test_redemption.py and was wrongly rejected."""

    draft = paired_draft()
    draft["private"]["expected_changes"].append(
        {"path": "tests/test_new_rules.py", "expectation": "New regression tests for the requirements."}
    )
    scenario, repairs = assemble_backend(draft, attempt_id="n1", difficulty="junior")
    assert "tests/test_new_rules.py" in [item["path"] for item in scenario["private_context"]["expected_changes"]]
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)


@pytest.mark.parametrize("comment", [
    "# CURRENT IMPLEMENTATION: Missing validation and idempotency",
    "# Current logic is missing validation for min amount, balance, and transaction uniqueness",
    "# Amount is not validated here yet",
])
def test_hint_phrases_anywhere_in_a_comment_are_rejected(comment):
    draft = paired_draft()
    target = next(item for item in draft["project"]["files"] if item["path"] == "services/user_service.py")
    target["content"] = comment + "\n" + target["content"]
    scenario, repairs = assemble_backend(draft, attempt_id="n2", difficulty="junior")
    with pytest.raises(GenerationAttemptError, match="reveals the solution in services/user_service.py"):
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_only_public_requirements_are_assessed():
    """Live draft 3 (2026-11-16) assessed missing-request_id handling that no requirement asked for."""

    from services.ai.scenario_drafts import BACKEND_DRAFT_SCHEMA

    assert "additional_criteria" not in BACKEND_DRAFT_SCHEMA["properties"]["private"]["properties"]
    draft = paired_draft()
    draft["private"]["additional_criteria"] = [
        {"criterion": "Unstated behaviour.", "evidence": "Code.", "files": ["services/user_service.py"]}
    ]
    scenario, _ = assemble_backend(draft, attempt_id="u1", difficulty="junior")
    assert len(scenario["private_context"]["assessment_criteria"]) == len(draft["requirements"])


UNUSED = "from dataclasses import dataclass\n\n\n@dataclass\nclass Ledger:\n    total: int = 0\n"


def test_an_unused_unreferenced_module_is_removed():
    """Live draft 1 (2026-11-16) shipped a models.py that nothing imported."""

    draft = paired_draft()
    draft["project"]["files"].append({"path": "services/ledger_models.py", "content": UNUSED})
    draft["readme"]["file_responsibilities"].append({"path": "services/ledger_models.py", "responsibility": "Ledger model."})
    scenario, repairs = assemble_backend(draft, attempt_id="u2", difficulty="junior")
    paths = [item["path"] for item in scenario["public_scenario"]["project"]["files"]]
    assert "services/ledger_models.py" not in paths
    assert "removed_unused_module:services/ledger_models.py" in repairs
    readme = next(item["content"] for item in scenario["public_scenario"]["project"]["files"] if item["path"] == "README.md")
    assert "ledger_models" not in readme
    accept_assembled(scenario, repairs, validate_generated_backend_scenario)


def test_an_unused_module_named_by_the_task_is_rejected_not_removed():
    draft = paired_draft()
    draft["project"]["files"].append({"path": "services/ledger_models.py", "content": UNUSED})
    draft["readme"]["file_responsibilities"].append({"path": "services/ledger_models.py", "responsibility": "Ledger model."})
    draft["email_body"] += "\n\nThe ledger model lives in services/ledger_models.py."
    scenario, repairs = assemble_backend(draft, attempt_id="u3", difficulty="junior")
    with pytest.raises(GenerationAttemptError, match="ledger_models.py is not imported"):
        accept_assembled(scenario, repairs, validate_generated_backend_scenario)
