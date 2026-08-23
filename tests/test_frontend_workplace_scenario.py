from copy import deepcopy
import json

import pytest

from services.frontend_workplace_scenario_service import (
    deterministic_frontend_scenario,
    validate_frontend_workplace_scenario,
)
from services.backend_demo_scenario_service import (
    get_backend_demo_workplace_scenario,
)
from services.scenario_generation_service import (
    ScenarioGenerationError,
    validate_workplace_scenario,
)


def test_fallback_has_exactly_five_emails_and_tasks():
    scenario = deterministic_frontend_scenario("Example Co", "attempt-1")
    public = scenario["public_scenario"]
    assert len(public["inbox_emails"]) == 5
    assert len(public["frontend_tasks"]) == 5
    assert [task["step"] for task in public["frontend_tasks"]] == [1, 2, 3, 4, 5]


def test_public_payload_does_not_leak_private_rubric():
    scenario = validate_frontend_workplace_scenario(
        deterministic_frontend_scenario("Example Co", "attempt-2")
    )
    public = json.dumps(scenario["public_scenario"])
    assert "expected_patch" not in public
    assert "root_cause" not in public


def test_fallback_payload_is_json_and_firebase_key_safe():
    scenario = deterministic_frontend_scenario("Live Company, Inc.", "attempt-3")
    json.dumps(scenario["public_scenario"])
    json.dumps(scenario["private_context"])

    def assert_safe(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key and not any(character in key for character in '.#$/[]')
                assert_safe(child)
        elif isinstance(value, list):
            for child in value:
                assert_safe(child)

    assert_safe(scenario)


@pytest.mark.parametrize(
    ("path", "expected_message"),
    [
        ("../index.html", "unsafe project path"),
        ("notes.py", "unsupported file type"),
    ],
)
def test_frontend_project_rejects_unsafe_or_unsupported_paths(
    path,
    expected_message,
):
    scenario = deterministic_frontend_scenario("Example Co", "unsafe-path")
    malformed = deepcopy(scenario)
    target_index = 0 if path.startswith("..") else 3
    malformed["public_scenario"]["project"]["files"][target_index][
        "path"
    ] = path

    with pytest.raises(ScenarioGenerationError, match=expected_message):
        validate_frontend_workplace_scenario(malformed)


def test_frontend_extensions_do_not_broaden_backend_validation():
    backend_scenario = get_backend_demo_workplace_scenario(
        attempt_id="backend-extension-policy"
    )
    backend_scenario["public_scenario"]["project"]["files"].append(
        {"path": "templates/profile.html", "content": "<p>Profile</p>"}
    )

    with pytest.raises(ScenarioGenerationError, match="unsupported file type"):
        validate_workplace_scenario(backend_scenario)


def test_frontend_project_rejects_duplicates_and_missing_required_files():
    scenario = deterministic_frontend_scenario("Example Co", "project-files")

    duplicate = deepcopy(scenario)
    duplicate["public_scenario"]["project"]["files"][1]["path"] = "index.html"
    with pytest.raises(ScenarioGenerationError, match="duplicate project file"):
        validate_frontend_workplace_scenario(duplicate)

    missing = deepcopy(scenario)
    missing["public_scenario"]["project"]["files"] = [
        file_item
        for file_item in missing["public_scenario"]["project"]["files"]
        if file_item["path"] != "product.js"
    ]
    with pytest.raises(ScenarioGenerationError, match="missing required files"):
        validate_frontend_workplace_scenario(missing)


def test_frontend_scenario_rejects_invalid_steps_and_applications():
    scenario = deterministic_frontend_scenario("Example Co", "task-rules")

    unordered = deepcopy(scenario)
    unordered["public_scenario"]["frontend_tasks"][1]["step"] = 4
    with pytest.raises(ScenarioGenerationError, match="ordered steps"):
        validate_frontend_workplace_scenario(unordered)

    invalid_application = deepcopy(scenario)
    invalid_application["public_scenario"]["frontend_tasks"][0][
        "application"
    ] = "terminal"
    with pytest.raises(ScenarioGenerationError, match="application is invalid"):
        validate_frontend_workplace_scenario(invalid_application)


def test_frontend_scenario_rejects_invalid_email_incident_structure():
    scenario = deterministic_frontend_scenario("Example Co", "email-rules")

    duplicate_ids = deepcopy(scenario)
    duplicate_ids["public_scenario"]["inbox_emails"][1]["id"] = (
        duplicate_ids["public_scenario"]["inbox_emails"][0]["id"]
    )
    with pytest.raises(ScenarioGenerationError, match="IDs must be unique"):
        validate_frontend_workplace_scenario(duplicate_ids)

    wrong_critical_ticket = deepcopy(scenario)
    wrong_critical_ticket["public_scenario"]["inbox_emails"][0][
        "linked_ticket_id"
    ] = "FE-OTHER"
    with pytest.raises(ScenarioGenerationError, match="critical email"):
        validate_frontend_workplace_scenario(wrong_critical_ticket)


def test_frontend_scenario_rejects_unsafe_commands_and_invalid_viewports():
    scenario = deterministic_frontend_scenario("Example Co", "metadata-rules")

    unsafe_command = deepcopy(scenario)
    unsafe_command["public_scenario"]["allowed_terminal_commands"].append(
        "sudo npm test"
    )
    with pytest.raises(ScenarioGenerationError, match="terminal command"):
        validate_frontend_workplace_scenario(unsafe_command)

    invalid_viewport = deepcopy(scenario)
    invalid_viewport["public_scenario"]["viewport_presets"]["mobile"] = "375"
    with pytest.raises(ScenarioGenerationError, match="viewport presets"):
        validate_frontend_workplace_scenario(invalid_viewport)


def test_frontend_scenario_rejects_private_leaks_and_unsafe_firebase_keys():
    scenario = deterministic_frontend_scenario("Example Co", "privacy-rules")

    leaked = deepcopy(scenario)
    leaked["public_scenario"]["evaluation"] = {
        "expected_patch": {"product_js": "private"}
    }
    with pytest.raises(ScenarioGenerationError, match="private solution fields"):
        validate_frontend_workplace_scenario(leaked)

    unsafe_private_key = deepcopy(scenario)
    unsafe_private_key["private_context"]["expected_patch"] = {
        "product.js": "private"
    }
    with pytest.raises(ScenarioGenerationError, match="Firebase-safe"):
        validate_frontend_workplace_scenario(unsafe_private_key)


def test_frontend_scenario_rejects_oversized_project_files():
    scenario = deterministic_frontend_scenario("Example Co", "file-size")
    malformed = deepcopy(scenario)
    malformed["public_scenario"]["project"]["files"][0]["content"] = (
        "x" * 20_001
    )

    with pytest.raises(ScenarioGenerationError, match="oversized project file"):
        validate_frontend_workplace_scenario(malformed)
