from typing import Literal

from pydantic import BaseModel, Field


class ApiEndpoint(BaseModel):
    """API endpoint tested during Step 4."""

    method: Literal["POST"]
    path: Literal["/api/checkout"]


class ApiTestResult(BaseModel):
    """Result of one required API test."""

    test_id: Literal[
        "valid_cart",
        "missing_product_id",
        "null_product_id",
    ]

    expected_status: int = Field(
        ge=100,
        le=599,
    )

    actual_status: int = Field(
        ge=100,
        le=599,
    )

    passed: bool


class ApiTestingResponse(BaseModel):
    """Validated response from the Step 4 API workspace."""

    task_type: Literal["api_testing"]

    endpoint: ApiEndpoint

    tests_run: list[ApiTestResult] = Field(
        min_length=3,
        max_length=3,
    )

    request_count: int = Field(
        ge=3,
        le=100,
    )

    all_tests_passed: Literal[True]

    release_decision: Literal["ready_for_review"]