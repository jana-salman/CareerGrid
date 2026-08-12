import json

from pydantic import ValidationError

from schemas.ux_research_response_schema import UXResearchResponse


VALID_PROBLEMS = {
    "forced_account_creation",
    "payment_options",
    "product_images",
    "search_functionality",
}


class UXResearchValidationError(ValueError):
    """Raised when the UX research response is invalid."""


def validate_ux_research_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structured UX research response submitted by Step 2.
    """

    try:
        parsed_answer = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise UXResearchValidationError(
            "The UX research response could not be read."
        ) from error


    try:
        response = UXResearchResponse.model_validate(
            parsed_answer
        )

    except ValidationError as error:
        raise UXResearchValidationError(
            "Please complete the UX research investigation "
            "before continuing."
        ) from error


    if response.selected_problem not in VALID_PROBLEMS:
        raise UXResearchValidationError(
            "Please identify the primary UX problem."
        )


    if not response.opened_evidence:
        raise UXResearchValidationError(
            "Review at least one research source before continuing."
        )


    if not response.selected_evidence:
        raise UXResearchValidationError(
            "Select evidence that supports your diagnosis."
        )


    if not response.research_finding.strip():
        raise UXResearchValidationError(
            "Write a short research finding before continuing."
        )


    return response.model_dump()
