import json

from pydantic import ValidationError

from schemas.team_chat_response_schema import (
    TeamChatResponse,
)


class TeamChatResponseValidationError(ValueError):
    """Raised when the Step 5 team update is invalid."""


REQUIRED_CHECKLIST_ORDER = [
    "root_cause_identified",
    "fix_implemented",
    "valid_payload_tested",
    "invalid_payload_tested",
    "server_error_prevented",
]


INCIDENT_STATUS_LABELS = {
    "resolved": "Resolved",
    "needs_further_testing": "Needs further testing",
    "blocked": "Blocked",
}


RECOMMENDATION_LABELS = {
    "ready_for_review": "Ready for code review",
    "needs_more_testing": "Needs more testing",
    "do_not_release": "Do not release",
}


def validate_team_chat_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate and normalize the interactive Step 5 response.

    The final message is rebuilt on the server instead of trusting
    the message text sent by the browser.
    """

    try:
        submitted_data = json.loads(
            raw_answer
        )

    except json.JSONDecodeError as error:
        raise TeamChatResponseValidationError(
            "The team update format is invalid."
        ) from error

    if not isinstance(submitted_data, dict):
        raise TeamChatResponseValidationError(
            "The team update must be an object."
        )

    text_fields = [
        "root_cause",
        "fix_summary",
        "testing_summary",
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
        response = TeamChatResponse.model_validate(
            submitted_data
        )

    except ValidationError as error:
        raise TeamChatResponseValidationError(
            "Complete every part of the update and preview it "
            "before finishing the simulation."
        ) from error

    normalized_response = response.model_dump()

    # Use a consistent checklist order.
    normalized_response["checklist"] = (
        REQUIRED_CHECKLIST_ORDER
    )

    incident_status_label = (
        INCIDENT_STATUS_LABELS[
            response.incident_status
        ]
    )

    recommendation_label = (
        RECOMMENDATION_LABELS[
            response.release_recommendation
        ]
    )

    # Rebuild the final message using server-validated fields.
    normalized_response["message"] = "\n".join([
        f"Incident status: {incident_status_label}",
        "",
        "Root cause:",
        response.root_cause,
        "",
        "Fix implemented:",
        response.fix_summary,
        "",
        "Testing completed:",
        response.testing_summary,
        "",
        (
            "Release recommendation: "
            f"{recommendation_label}"
        ),
    ])

    normalized_response["server_verified"] = True

    return normalized_response