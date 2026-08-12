import json

from pydantic import ValidationError

from schemas.ux_flow_response_schema import UXFlowResponse


VALID_FLOW_STEPS = {
    "cart",
    "shipping",
    "guest_checkout",
    "sign_in",
    "create_account",
    "payment",
    "confirmation",
    "newsletter",
}


class UXFlowValidationError(ValueError):
    """Raised when the UX flow response is invalid."""


def validate_ux_flow_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structured UX flow-builder response.
    """

    try:
        parsed_answer = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise UXFlowValidationError(
            "The UX flow response could not be read."
        ) from error


    try:
        response = UXFlowResponse.model_validate(
            parsed_answer
        )

    except ValidationError as error:
        raise UXFlowValidationError(
            "Please complete the checkout flow before continuing."
        ) from error


    for step in response.selected_flow:
        if step not in VALID_FLOW_STEPS:
            raise UXFlowValidationError(
                "The checkout flow contains an invalid step."
            )


    if response.selected_flow[0] != "cart":
        raise UXFlowValidationError(
            "The redesigned checkout flow should begin with the cart."
        )


    if "shipping" not in response.selected_flow:
        raise UXFlowValidationError(
            "The redesigned checkout flow must include shipping."
        )


    if "guest_checkout" not in response.selected_flow:
        raise UXFlowValidationError(
            "The redesigned flow must include a guest checkout option."
        )


    if "payment" not in response.selected_flow:
        raise UXFlowValidationError(
            "The redesigned checkout flow must include payment."
        )


    if "confirmation" not in response.selected_flow:
        raise UXFlowValidationError(
            "The redesigned checkout flow must include confirmation."
        )


    if response.flow_test_runs < 1:
        raise UXFlowValidationError(
            "Test the redesigned checkout flow before continuing."
        )


    return response.model_dump()