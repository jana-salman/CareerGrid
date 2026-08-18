import json

from services.frontend_workplace_scenario_service import (
    deterministic_frontend_scenario,
    validate_frontend_workplace_scenario,
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
