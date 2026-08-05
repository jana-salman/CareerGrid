import json

from pydantic import ValidationError

from schemas.frontend_browser_testing_response_schema import (
    FrontendBrowserTestingResponse,
)


class FrontendBrowserTestingValidationError(ValueError):
    """Raised only when the response is structurally unusable."""


REQUIRED_TEST_IDS = [
    "desktop_mouse",
    "mobile_viewport",
    "keyboard_accessibility",
]


def validate_frontend_browser_testing_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate the structure of the Step 4 submission and record the
    browser test results. The user may proceed even if a test failed
    or was not run. The final AI evaluation scores the outcome.
    """

    try:
        submitted_data = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise FrontendBrowserTestingValidationError(
            "The browser testing response could not be read."
        ) from error

    if not isinstance(submitted_data, dict):
        raise FrontendBrowserTestingValidationError(
            "The browser testing response must be an object."
        )

    try:
        response = (
            FrontendBrowserTestingResponse.model_validate(
                submitted_data
            )
        )

    except ValidationError as error:
        raise FrontendBrowserTestingValidationError(
            "The browser testing response was not in the "
            "expected format."
        ) from error

    # Keep only the last result per unique test id.
    unique_tests = {}

    for test in response.tests_run:
        unique_tests[test.test_id] = {
            "test_id": test.test_id,
            "expected_outcome": test.expected_outcome,
            "actual_outcome": test.actual_outcome,
            "passed": test.actual_outcome == "pass",
        }

    normalized_tests = list(unique_tests.values())

    passed_count = sum(
        1 for test in normalized_tests if test["passed"]
    )

    normalized_response = response.model_dump()

    normalized_response["tests_run"] = normalized_tests
    normalized_response["all_tests_passed"] = (
        passed_count == len(REQUIRED_TEST_IDS)
    )
    normalized_response["passed_test_count"] = passed_count
    normalized_response["server_verified"] = True

    return normalized_response