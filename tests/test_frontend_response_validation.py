import pytest

from services.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)


def valid_responses_through_step_three():
    responses = {}
    responses["step_1"] = validate_frontend_progress(
        step=1,
        payload={
            "opened_email_ids": ["buy-now-incident"],
            "selected_email_id": "buy-now-incident",
            "selected_priority": "Critical",
            "selected_action": "Reproduce",
            "written_response": (
                "I will reproduce and inspect the frontend evidence."
            ),
        },
        existing_responses=responses,
    )
    responses["step_2"] = validate_frontend_progress(
        step=2,
        payload={
            "pages_inspected": ["product"],
            "viewports_tested": ["Desktop", "Mobile"],
            "evidence_opened": ["Console", "Elements"],
            "selected_root_cause": "selector mismatch",
            "proposed_next_action": "Patch the selector safely",
            "investigation_summary": (
                "The Buy Now button ID does not match the JavaScript selector."
            ),
        },
        existing_responses=responses,
    )
    responses["step_3"] = validate_frontend_progress(
        step=3,
        payload={
            "files_opened": ["product.js"],
            "changed_files": {
                "product.js": (
                    "document.addEventListener('DOMContentLoaded', () => { "
                    "const button = document.querySelector('#buy-now-btn'); "
                    "if (button) button.addEventListener('click', "
                    "openCheckoutPanel); });"
                )
            },
            "fix_explanation": (
                "Use the semantic button ID and guard initialization."
            ),
        },
        existing_responses=responses,
    )
    return responses


def test_tasks_must_be_completed_in_sequence():
    with pytest.raises(FrontendProgressValidationError):
        validate_frontend_progress(step=2, payload={}, existing_responses={})


def test_verification_is_derived_from_saved_patch():
    responses = valid_responses_through_step_three()
    result = validate_frontend_progress(
        step=4,
        payload={
            "commands_run": ["npm test"],
            "tests_performed": ["mouse"],
            "viewport_checks": ["Desktop", "Mobile"],
            "accessibility_checks": ["keyboard"],
            "release_decision": "Ready",
        },
        existing_responses=responses,
    )
    assert result["all_required_tests_passed"] is True


def test_unsafe_terminal_command_is_rejected():
    responses = valid_responses_through_step_three()
    with pytest.raises(FrontendProgressValidationError):
        validate_frontend_progress(
            step=4,
            payload={
                "commands_run": ["rm -rf ."],
                "release_decision": "Ready",
            },
            existing_responses=responses,
        )


def test_frontend_workflow_validates_all_five_steps_in_sequence():
    responses = valid_responses_through_step_three()
    responses["step_4"] = validate_frontend_progress(
        step=4,
        payload={
            "commands_run": ["npm test", "npm run lint", "npm run build"],
            "tests_performed": ["mouse", "repeat click"],
            "viewport_checks": ["Desktop", "Mobile"],
            "accessibility_checks": ["keyboard", "focus"],
            "release_decision": "Ready",
        },
        existing_responses=responses,
    )

    responses["step_5"] = validate_frontend_progress(
        step=5,
        payload={
            "reviewed_files": ["product.js"],
            "commit_message": "Fix Buy Now selector",
            "pr_title": "Restore checkout interaction",
            "pr_description": (
                "Use the semantic Buy Now selector, retain the native button, "
                "and guard initialization before attaching the click listener."
            ),
            "testing_checklist": ["npm test", "npm run lint", "npm run build"],
            "release_recommendation": "Ready",
            "final_team_message": (
                "The focused selector fix is verified across desktop, mobile, "
                "keyboard, repeated-click, lint, test, and build checks."
            ),
        },
        existing_responses=responses,
    )

    assert [responses[f"step_{step}"]["step"] for step in range(1, 6)] == [
        1,
        2,
        3,
        4,
        5,
    ]
    assert responses["step_5"]["source_step_3_files"] == ["product.js"]
    assert responses["step_5"]["source_step_4_results"]

