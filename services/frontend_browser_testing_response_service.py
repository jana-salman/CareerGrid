import json

from pydantic import ValidationError

from schemas.frontend_browser_testing_response_schema import (
    FrontendBrowserTestingResponse,
)


class FrontendBrowserTestingValidationError(ValueError):
    """Raised when the browser testing response is invalid."""


REQUIRED_TESTS = {
    "desktop_mouse": {
        "expected_outcome": "pass",
        "actual_outcome": "pass",
    },
    "mobile_viewport": {
        "expected_outcome": "pass",
        "actual_outcome": "pass",
    },
    "keyboard_accessibility": {
        "expected_outcome": "pass",
        "actual_outcome": "pass",
    },
}


def validate_frontend_browser_testing_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate and normalize the Step 4 browser testing submission.

    The browser submission is checked again on the server so users
    cannot skip required tests by changing the page JavaScript.
    """

    try:
        submitted_data = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise FrontendBrowserTestingValidationError(
            "The browser testing response format is invalid."
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
            "Complete all required browser tests before continuing."
        ) from error

    submitted_tests = {
        test.test_id: test
        for test in response.tests_run
    }

    # Three submitted entries must also be three unique test cases.
    if len(submitted_tests) != len(REQUIRED_TESTS):
        raise FrontendBrowserTestingValidationError(
            "Each required browser test must be completed once."
        )

    normalized_tests = []

    for test_id, expected_result in REQUIRED_TESTS.items():
        submitted_test = submitted_tests.get(test_id)

        if submitted_test is None:
            raise FrontendBrowserTestingValidationError(
                f"The required test '{test_id}' was not completed."
            )

        correct_result = (
            submitted_test.expected_outcome
            == expected_result["expected_outcome"]
            and submitted_test.actual_outcome
            == expected_result["actual_outcome"]
            and submitted_test.passed is True
        )

        if not correct_result:
            raise FrontendBrowserTestingValidationError(
                "One or more browser test results are incorrect."
            )

        normalized_tests.append({
            "test_id": test_id,
            "expected_outcome": (
                expected_result["expected_outcome"]
            ),
            "actual_outcome": (
                expected_result["actual_outcome"]
            ),
            "passed": True,
        })

    normalized_response = response.model_dump()

    # Use the server-verified test order and values.
    normalized_response["tests_run"] = normalized_tests
    normalized_response["all_tests_passed"] = True
    normalized_response["release_decision"] = (
        "ready_for_release"
    )
    normalized_response["server_verified"] = True

    return normalized_response