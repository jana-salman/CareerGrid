from typing import Literal

from pydantic import BaseModel, Field


class BrowserTestTarget(BaseModel):
    """The component tested during Step 4."""

    component: Literal["buy_now_button"]
    page: Literal["product_page"]


class BrowserTestResult(BaseModel):
    """Result of one required browser test."""

    test_id: Literal[
        "desktop_mouse",
        "mobile_viewport",
        "keyboard_accessibility",
    ]

    expected_outcome: Literal["pass"]

    actual_outcome: Literal["pass"]

    passed: bool


class FrontendBrowserTestingResponse(BaseModel):
    """Validated response from the Step 4 browser workspace."""

    task_type: Literal["frontend_browser_testing"]

    target: BrowserTestTarget

    tests_run: list[BrowserTestResult] = Field(
        min_length=3,
        max_length=3,
    )

    test_count: int = Field(
        ge=3,
        le=100,
    )

    all_tests_passed: Literal[True]

    release_decision: Literal["ready_for_release"]
    