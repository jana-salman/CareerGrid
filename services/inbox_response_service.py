import json
from typing import Any

from pydantic import ValidationError

from schemas.inbox_response_schema import InboxResponse


class InboxResponseValidationError(ValueError):
    """Raised when an inbox response fails validation."""


def validate_inbox_response(
    *,
    raw_answer: str,
    generated_task: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate the inbox response against the saved generated task.

    This prevents users from modifying the hidden form data and
    submitting invalid email IDs, actions, or priority orders.
    """

    if not isinstance(generated_task, dict):
        raise RuntimeError(
            "The generated inbox task could not be loaded."
        )

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise InboxResponseValidationError(
            "The inbox response format is invalid."
        ) from error

    try:
        response = InboxResponse.model_validate(
            submitted_data
        )
    except ValidationError as error:
        raise InboxResponseValidationError(
            "Please complete every part of the inbox task."
        ) from error

    generated_emails = generated_task.get("emails", [])

    if not isinstance(generated_emails, list):
        raise RuntimeError(
            "The generated inbox task contains invalid email data."
        )

    valid_email_ids = [
        email.get("id")
        for email in generated_emails
        if isinstance(email, dict) and email.get("id")
    ]

    if not valid_email_ids:
        raise RuntimeError(
            "The generated inbox task contains no valid emails."
        )

    if len(valid_email_ids) != len(set(valid_email_ids)):
        raise RuntimeError(
            "The generated inbox contains duplicate email IDs."
        )

    valid_email_id_set = set(valid_email_ids)

    opened_email_ids = response.opened_emails

    if len(opened_email_ids) != len(set(opened_email_ids)):
        raise InboxResponseValidationError(
            "The opened email list contains duplicate entries."
        )

    if not set(opened_email_ids).issubset(
        valid_email_id_set
    ):
        raise InboxResponseValidationError(
            "The response contains an invalid email."
        )

    priority_order = response.priority_order

    if len(priority_order) != len(valid_email_ids):
        raise InboxResponseValidationError(
            "Please prioritize every email before continuing."
        )

    if len(priority_order) != len(set(priority_order)):
        raise InboxResponseValidationError(
            "Each email can appear only once in the priority order."
        )

    if set(priority_order) != valid_email_id_set:
        raise InboxResponseValidationError(
            "The submitted priority order is invalid."
        )

    available_actions = generated_task.get(
        "available_first_actions",
        [],
    )

    if not isinstance(available_actions, list):
        raise RuntimeError(
            "The generated inbox contains invalid actions."
        )

    if response.selected_action not in available_actions:
        raise InboxResponseValidationError(
            "The selected action is not valid for this task."
        )

    normalized_response = response.model_dump()

    normalized_response["written_reply"] = (
        normalized_response["written_reply"].strip()
    )

    return normalized_response