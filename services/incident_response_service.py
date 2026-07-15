import json

from pydantic import ValidationError

from schemas.incident_response_schema import (
    IncidentResponse,
)


class IncidentResponseValidationError(ValueError):
    """Raised when an incident response is invalid."""


def validate_incident_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate and normalize a submitted incident response.
    """

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise IncidentResponseValidationError(
            "The incident response format is invalid."
        ) from error

    if not isinstance(submitted_data, dict):
        raise IncidentResponseValidationError(
            "The incident response must be an object."
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
            IncidentResponse.model_validate(
                submitted_data
            )
        )
    except ValidationError as error:
        raise IncidentResponseValidationError(
            "Please complete every part of the investigation."
        ) from error

    return validated_response.model_dump()