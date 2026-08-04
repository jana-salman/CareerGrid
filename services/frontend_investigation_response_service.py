import json

from pydantic import ValidationError

from schemas.frontend_investigation_response_schema import (
    FrontendInvestigationResponse,
)


class FrontendInvestigationValidationError(ValueError):
    """Raised when a frontend investigation response is invalid."""


def validate_frontend_investigation_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate and normalize a submitted frontend investigation.
    """

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise FrontendInvestigationValidationError(
            "The investigation response format is invalid."
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
            "Please complete every part of the investigation."
        ) from error

    return validated_response.model_dump()