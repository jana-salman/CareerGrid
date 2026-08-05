import json

from pydantic import ValidationError

from schemas.frontend_team_chat_response_schema import (
    FrontendTeamChatResponse,
)


class FrontendTeamChatValidationError(ValueError):
    """Raised only when the response is structurally unusable."""


REQUIRED_CHECKLIST_ORDER = [
    "root_cause_identified",
    "selector_fixed",
    "dom_ready_handled",
    "desktop_tested",
    "mobile_tested",
    "keyboard_tested",
]


ISSUE_STATUS_LABELS = {
    "resolved": "Resolved",
    "needs_further_testing": "Needs further testing",
    "blocked": "Blocked",
}


RECOMMENDATION_LABELS = {
    "ready_for_review": "Ready for code review",
    "needs_more_testing": "Needs more testing",
    "do_not_release": "Do not release",
}


def validate_frontend_team_chat_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structure of the Step 5 update and rebuild the
    final message from the submitted fields. The update may be
    incomplete; the final AI evaluation judges its quality.
    """

    try:
        submitted_data = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise FrontendTeamChatValidationError(
            "The team update could not be read."
        ) from error

    if not isinstance(submitted_data, dict):
        raise FrontendTeamChatValidationError(
            "The team update must be an object."
        )

    text_fields = [
        "root_cause",
        "fix_summary",
        "testing_summary",
        "accessibility_summary",
        "message",
    ]

    for field_name in text_fields:
        field_value = submitted_data.get(
            field_name,
            "",
        )

        if isinstance(field_value, str):
            submitted_data[field_name] = (
                field_value.strip()
            )

    try:
        response = FrontendTeamChatResponse.model_validate(
            submitted_data
        )

    except ValidationError as error:
        raise FrontendTeamChatValidationError(
            "The team update was not in the expected format."
        ) from error

    normalized_response = response.model_dump()

    # Keep the confirmed checklist in a consistent order.
    confirmed = set(response.checklist)
    normalized_response["checklist"] = [
        item
        for item in REQUIRED_CHECKLIST_ORDER
        if item in confirmed
    ]

    # Record how complete the checklist is for the AI evaluation.
    normalized_response["checklist_complete"] = (
        len(normalized_response["checklist"])
        == len(REQUIRED_CHECKLIST_ORDER)
    )

    issue_status_label = ISSUE_STATUS_LABELS[
        response.issue_status
    ]

    recommendation_label = RECOMMENDATION_LABELS[
        response.release_recommendation
    ]

    # Rebuild the final message using the server-validated fields
    # instead of trusting the browser text.
    normalized_response["message"] = "\n".join([
        f"Issue status: {issue_status_label}",
        "",
        "Root cause:",
        response.root_cause or "(not provided)",
        "",
        "Fix implemented:",
        response.fix_summary or "(not provided)",
        "",
        "Browser testing completed:",
        response.testing_summary or "(not provided)",
        "",
        "Accessibility and responsive design:",
        response.accessibility_summary or "(not provided)",
        "",
        (
            "Release recommendation: "
            f"{recommendation_label}"
        ),
    ])

    normalized_response["server_verified"] = True

    return normalized_response