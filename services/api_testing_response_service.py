import json

from pydantic import ValidationError

from schemas.api_testing_response_schema import (
    ApiTestingResponse,
)


class ApiTestingResponseValidationError(ValueError):
    """Raised when the API testing response is invalid."""


REQUIRED_TESTS = {
    "valid_cart": {
        "expected_status": 201,
        "actual_status": 201,
    },
    "missing_product_id": {
        "expected_status": 400,
        "actual_status": 400,
    },
    "null_product_id": {
        "expected_status": 400,
        "actual_status": 400,
    },
}


def validate_api_testing_response(
    *,
    raw_answer: str,
) -> dict:
    """
    Validate and normalize the Step 4 API testing submission.

    The browser submission is checked again on the server so users
    cannot skip required tests by changing the page JavaScript.
    """

    try:
        submitted_data = json.loads(raw_answer)

    except json.JSONDecodeError as error:
        raise ApiTestingResponseValidationError(
            "The API testing response format is invalid."
        ) from error

    if not isinstance(submitted_data, dict):
        raise ApiTestingResponseValidationError(
            "The API testing response must be an object."
        )

    try:
        response = ApiTestingResponse.model_validate(
            submitted_data
        )

    except ValidationError as error:
        raise ApiTestingResponseValidationError(
            "Complete all required API tests before continuing."
        ) from error

    submitted_tests = {
        test.test_id: test
        for test in response.tests_run
    }

    # Three submitted entries must also be three unique test cases.
    if len(submitted_tests) != len(REQUIRED_TESTS):
        raise ApiTestingResponseValidationError(
            "Each required API test must be completed once."
        )

    normalized_tests = []

    for test_id, expected_result in REQUIRED_TESTS.items():
        submitted_test = submitted_tests.get(test_id)

        if submitted_test is None:
            raise ApiTestingResponseValidationError(
                f"The required test '{test_id}' was not completed."
            )

        correct_result = (
            submitted_test.expected_status
            == expected_result["expected_status"]
            and submitted_test.actual_status
            == expected_result["actual_status"]
            and submitted_test.passed is True
        )

        if not correct_result:
            raise ApiTestingResponseValidationError(
                "One or more API test results are incorrect."
            )

        normalized_tests.append({
            "test_id": test_id,
            "expected_status": (
                expected_result["expected_status"]
            ),
            "actual_status": (
                expected_result["actual_status"]
            ),
            "passed": True,
        })

    normalized_response = response.model_dump()

    # Use the server-verified test order and values.
    normalized_response["tests_run"] = normalized_tests
    normalized_response["all_tests_passed"] = True
    normalized_response["release_decision"] = (
        "ready_for_review"
    )
    normalized_response["server_verified"] = True

    return normalized_response