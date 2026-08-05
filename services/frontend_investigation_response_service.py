import json

from pydantic import ValidationError

from schemas.frontend_investigation_response_schema import (
    FrontendInvestigationResponse,
)


class FrontendInvestigationValidationError(ValueError):
    """Raised only when the response is structurally unusable."""


# The expected (correct) diagnosis, used to record whether the user
# was right. It is NOT used to block progress.
EXPECTED = {
    "selected_html_id": "buy-now-btn",
    "selected_js_selector": "#checkout-btn",
    "selected_root_cause": "selector_id_mismatch",
    "selected_null_reason": "element_not_found",
    "selected_failure_mechanism": "addeventlistener_on_null",
}


def validate_frontend_investigation_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structure of the investigation response and record
    the user's selections. The user is allowed to be wrong.
    """

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise FrontendInvestigationValidationError(
            "The investigation response could not be read."
        ) from error

    if not isinstance(submitted_data, dict):
        raise FrontendInvestigationValidationError(
            "The investigation response must be an object."
        )

    technical_finding = submitted_data.get(
        "technical_finding",
        "",
    )

    if isinstance(technical_finding, str):
        submitted_data["technical_finding"] = (
            technical_finding.strip()
        )

    try:
        validated_response = (
            FrontendInvestigationResponse.model_validate(
                submitted_data
            )
        )
    except ValidationError as error:
        raise FrontendInvestigationValidationError(
            "The investigation response was not in the expected "
            "format."
        ) from error

    normalized_response = validated_response.model_dump()

    # Keep the counters internally consistent without rejecting.
    if (
        normalized_response["incorrect_diagnosis_attempts"]
        > normalized_response["diagnosis_attempts"]
    ):
        normalized_response["incorrect_diagnosis_attempts"] = (
            normalized_response["diagnosis_attempts"]
        )

    # Record whether the diagnosis matched the expected answer so the
    # AI evaluation has clear context. This does not block progress.
    normalized_response["diagnosis_is_correct"] = all(
        normalized_response.get(field) == expected_value
        for field, expected_value in EXPECTED.items()
    )

    return normalized_response