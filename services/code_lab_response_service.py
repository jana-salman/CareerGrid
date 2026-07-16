import json
import re

from pydantic import ValidationError

from schemas.code_lab_response_schema import (
    CodeLabResponse,
)


class CodeLabResponseValidationError(ValueError):
    """Raised when a Code Lab response is invalid."""


REQUIRED_TESTS = [
    "valid_cart",
    "missing_product_id",
    "no_server_crash",
]


def _analyze_submitted_code(
    code: str,
) -> dict[str, bool]:
    """
    Independently evaluate the submitted code.

    This repeats the important checks on the server instead of
    trusting the JavaScript test results submitted by the browser.
    """

    has_order_creation = bool(
        re.search(
            r"create_order_item\s*\(\s*product_id\s*\)",
            code,
        )
    )

    has_success_response = bool(
        re.search(
            r"return[\s\S]*,\s*201\b",
            code,
        )
    )

    uses_safe_get = bool(
        re.search(
            r"""item\s*\.\s*get\s*\(
                \s*["']product_id["']\s*
            \)""",
            code,
            re.VERBOSE,
        )
    )

    checks_missing_value = bool(
        re.search(
            r"""if\s+
                (
                    not\s+product_id
                    |
                    product_id\s+is\s+None
                    |
                    product_id\s*==\s*None
                )
                \s*:
            """,
            code,
            re.VERBOSE,
        )
    )

    checks_field_before_access = bool(
        re.search(
            r"""if\s+["']product_id["']
                \s+not\s+in\s+item\s*:
            """,
            code,
            re.VERBOSE,
        )
    )

    returns_client_error = bool(
        re.search(
            r"""(
                ,\s*400\b
                |
                ["']status["']\s*:\s*400\b
                |
                status_code\s*=\s*400\b
            )""",
            code,
            re.VERBOSE,
        )
    )

    uses_unsafe_direct_access = bool(
        re.search(
            r"""item\s*\[
                \s*["']product_id["']\s*
            \]""",
            code,
            re.VERBOSE,
        )
    )

    valid_cart_passes = (
        has_order_creation
        and has_success_response
    )

    missing_product_id_passes = (
        returns_client_error
        and (
            checks_field_before_access
            or (
                uses_safe_get
                and checks_missing_value
            )
        )
    )

    no_server_crash_passes = (
        not uses_unsafe_direct_access
        or checks_field_before_access
    )

    return {
        "valid_cart": valid_cart_passes,
        "missing_product_id": (
            missing_product_id_passes
        ),
        "no_server_crash": no_server_crash_passes,
    }


def validate_code_lab_response(
    *,
    raw_answer: str,
) -> dict:
    """Validate and normalize a Code Lab submission."""

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise CodeLabResponseValidationError(
            "The Code Lab response format is invalid."
        ) from error

    if not isinstance(submitted_data, dict):
        raise CodeLabResponseValidationError(
            "The Code Lab response must be an object."
        )

    submitted_code = submitted_data.get(
        "submitted_code",
        "",
    )

    if isinstance(submitted_code, str):
        submitted_data["submitted_code"] = (
            submitted_code.strip()
        )

    try:
        response = CodeLabResponse.model_validate(
            submitted_data
        )
    except ValidationError as error:
        raise CodeLabResponseValidationError(
            "The submitted Code Lab response is incomplete."
        ) from error

    test_results = _analyze_submitted_code(
        response.submitted_code
    )

    server_passed_tests = [
        test_id
        for test_id in REQUIRED_TESTS
        if test_results[test_id]
    ]

    if len(server_passed_tests) != len(REQUIRED_TESTS):
        raise CodeLabResponseValidationError(
            "The submitted code does not pass all required checks."
        )

    normalized_response = response.model_dump()

    # Never trust the browser's passed_tests value.
    normalized_response["passed_tests"] = (
        server_passed_tests
    )

    normalized_response["server_verified"] = True

    return normalized_response