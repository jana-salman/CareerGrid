import json
import re

from pydantic import ValidationError

from schemas.frontend_code_lab_response_schema import (
    FrontendCodeLabResponse,
)


class FrontendCodeLabValidationError(ValueError):
    """Raised only when the response is structurally unusable."""


CODE_CHECKS = [
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

    The results are recorded for the AI evaluation. They are NOT
    used to block the user from continuing.
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

    return {
        "correct_selector": (
            references_correct_id
            and not still_uses_wrong_selector
        ),
        "safe_initialization": uses_dom_ready,
        "existence_check": has_existence_check,
        "handler_attached": attaches_click_handler,
    }


def validate_frontend_code_lab_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structure of a Code Lab submission and record which
    checks the submitted code passes. The user may submit imperfect
    code and still continue.
    """

    try:
        submitted_data = json.loads(raw_answer)
    except json.JSONDecodeError as error:
        raise FrontendCodeLabValidationError(
            "The Code Lab response could not be read."
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
            "Please write some code before continuing."
        ) from error

    test_results = _analyze_submitted_code(
        response.submitted_code
    )

    server_passed_tests = [
        check_id
        for check_id in CODE_CHECKS
        if test_results[check_id]
    ]

    normalized_response = response.model_dump()

    # Record the server-verified results (never trust the browser).
    normalized_response["passed_tests"] = server_passed_tests
    normalized_response["all_checks_passed"] = (
        len(server_passed_tests) == len(CODE_CHECKS)
    )
    normalized_response["server_verified"] = True

    return normalized_response