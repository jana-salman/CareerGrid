import pytest

from services.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)


def valid_responses_through_step_three():
    responses = {}
    responses["step_1"] = validate_frontend_progress(step=1, payload={"opened_email_ids":["buy-now-incident"],"selected_email_id":"buy-now-incident","selected_priority":"Critical","selected_action":"Reproduce","written_response":"I will reproduce and inspect the frontend evidence."}, existing_responses=responses)
    responses["step_2"] = validate_frontend_progress(step=2, payload={"pages_inspected":["product"],"viewports_tested":["Desktop","Mobile"],"evidence_opened":["Console","Elements"],"selected_root_cause":"selector mismatch","proposed_next_action":"Patch the selector safely","investigation_summary":"The Buy Now button ID does not match the JavaScript selector."}, existing_responses=responses)
    responses["step_3"] = validate_frontend_progress(step=3, payload={"files_opened":["product.js"],"changed_files":{"product.js":"document.addEventListener('DOMContentLoaded', () => { const button = document.querySelector('#buy-now-btn'); if (button) button.addEventListener('click', openCheckoutPanel); });"},"fix_explanation":"Use the semantic button ID and guard initialization."}, existing_responses=responses)
    return responses


def test_tasks_must_be_completed_in_sequence():
    with pytest.raises(FrontendProgressValidationError):
        validate_frontend_progress(step=2, payload={}, existing_responses={})


def test_verification_is_derived_from_saved_patch():
    responses = valid_responses_through_step_three()
    result = validate_frontend_progress(step=4, payload={"commands_run":["npm test"],"tests_performed":["mouse"],"viewport_checks":["Desktop","Mobile"],"accessibility_checks":["keyboard"],"release_decision":"Ready"}, existing_responses=responses)
    assert result["all_required_tests_passed"] is True


def test_unsafe_terminal_command_is_rejected():
    responses = valid_responses_through_step_three()
    with pytest.raises(FrontendProgressValidationError):
        validate_frontend_progress(step=4, payload={"commands_run":["rm -rf ."],"release_decision":"Ready"}, existing_responses=responses)

