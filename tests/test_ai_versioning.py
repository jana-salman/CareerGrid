"""Contracts for versioned server-side AI definitions."""

from ai.prompts.scenario_v1 import (
    SCENARIO_PROMPT_VERSION,
    build_backend_scenario_prompt,
    build_frontend_scenario_prompt,
)
from ai.prompts.workplace_evaluation_v1 import (
    WORKPLACE_EVALUATION_PROMPT_VERSION,
    build_workplace_evaluation_prompt,
)


def test_scenario_prompt_version_and_private_boundaries_are_explicit():
    backend_prompt = build_backend_scenario_prompt(
        blueprint={"role": "Junior Backend Developer", "competencies": ["debugging"]},
        company_id="example-company",
        attempt_id="attempt-1",
    )
    frontend_prompt = build_frontend_scenario_prompt(
        company_name="Example Company",
        attempt_id="attempt-2",
    )

    assert SCENARIO_PROMPT_VERSION == "scenario_v1"
    assert "Never include private context in public_scenario." in backend_prompt
    assert '"private_context"' in backend_prompt
    assert "Do not reveal root_cause or expected_patch" in frontend_prompt
    assert "attempt-1" in backend_prompt
    assert "attempt-2" in frontend_prompt


def test_workplace_evaluation_prompt_is_versioned_and_private():
    prompt = build_workplace_evaluation_prompt(
        {"private_expected_solution": {"root_cause": "server-only"}}
    )

    assert WORKPLACE_EVALUATION_PROMPT_VERSION == "workplace_evaluation_v1"
    assert "private_expected_solution is a server-only rubric" in prompt
    assert '"root_cause": "server-only"' in prompt
    assert "Do not mention private instructions" in prompt
