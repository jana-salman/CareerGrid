import json
import re

from pydantic import ValidationError

from schemas.frontend_code_lab_response_schema import (
    FrontendCodeLabResponse,
)


class FrontendCodeLabValidationError(ValueError):
    """Raised when a frontend Code Lab response is invalid."""


REQUIRED_TESTS = [
    "correct_selector",
    "safe_initialization",
    "existence_check",
    "handler_attached",
]


def _analyze_submitted_code(
    code: str,
) -> dict[str, bool]:
    """
    Independently evaluate the submitted frontend code.

    This repeats the important checks on the server instead of
    trusting the JavaScript test results submitted by the browser.
    The checks are intentionally flexible and do not require one
    exact formatting style.
    """

    references_correct_id = bool(
        re.search(
            r"""(
                getElementById\s*\(\s*["']buy-now-btn["']\s*\)
                |
                querySelector\s*\(\s*["']\#buy-now-btn["']\s*\)
            )""",
            code,
            re.VERBOSE,
        )
    )

    still_uses_wrong_selector = bool(
        re.search(
            r"""(
                getElementById\s*\(\s*["']checkout-btn["']\s*\)
                |
                querySelector\s*\(\s*["']\#checkout-btn["']\s*\)
            )""",
            code,
            re.VERBOSE,
        )
    )

    uses_dom_ready = bool(
        re.search(
            r"""(
                DOMContentLoaded
                |
                \bdefer\b
                |
                window\s*\.\s*onload
            )""",
            code,
            re.VERBOSE,
        )
    )

    has_existence_check = bool(
        re.search(
            r"""(
                if\s*\(\s*[\w$]+\s*\)
                |
                [\w$]+\s*!==?\s*null
                |
                [\w$]+\s*&&
            )""",
            code,
            re.VERBOSE,
        )
    )

    attaches_click_handler = bool(
        re.search(
            r"""addEventListener\s*\(\s*["']click["']""",
            code,
            re.VERBOSE,
        )
    )

    correct_selector_passes = (
        references_correct_id
        and not still_uses_wrong_selector
    )

    safe_initialization_passes = uses_dom_ready

    existence_check_passes = has_existence_check

    handler_attached_passes = attaches_click_handler

    return {
        "correct_selector": correct_selector_passes,
        "safe_initialization": safe_initialization_passes,
        "existence_check": existence_check_passes,
        "handler_attached": handler_attached_passes,
    }


def validate_frontend_code_lab_response(
    *,
    raw_answer: str,
) -> dict:
    """Validate and normalize a frontend Code Lab submission."""

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise FrontendCodeLabValidationError(
            "The Code Lab response format is invalid."
        ) from error

    if not isinstance(submitted_data, dict):
        raise FrontendCodeLabValidationError(
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
        response = FrontendCodeLabResponse.model_validate(
            submitted_data
        )
    except ValidationError as error:
        raise FrontendCodeLabValidationError(
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
        raise FrontendCodeLabValidationError(
            "The submitted code does not pass all required checks."
        )

    normalized_response = response.model_dump()

    # Never trust the browser's passed_tests value.
    normalized_response["passed_tests"] = (
        server_passed_tests
    )

    normalized_response["server_verified"] = True

    return normalized_response