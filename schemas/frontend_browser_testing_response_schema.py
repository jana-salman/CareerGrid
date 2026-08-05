from typing import Literal

from pydantic import BaseModel, Field


class BrowserTestTarget(BaseModel):
    """The component tested during Step 4."""

    component: Literal["buy_now_button"]
    page: Literal["product_page"]


class BrowserTestResult(BaseModel):
    """Result of one browser test. Tests may pass or fail."""

    test_id: Literal[
        "desktop_mouse",
        "mobile_viewport",
        "keyboard_accessibility",
    ]

    expected_outcome: Literal["pass"] = "pass"

    actual_outcome: Literal["pass", "fail"]

    passed: bool


class FrontendBrowserTestingResponse(BaseModel):
    """
    Validated response from the Step 4 browser workspace.

    The user may proceed even if a test fails or not every test was
    run. The results are recorded and the release decision may be
    any valid option. The final AI evaluation scores the outcome.
    """

    task_type: Literal["frontend_browser_testing"]

    target: BrowserTestTarget

    tests_run: list[BrowserTestResult] = Field(
        default_factory=list,
        max_length=3,
    )

    test_count: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    all_tests_passed: bool = False

    release_decision: Literal[
        "ready_for_release",
        "needs_more_work",
        "do_not_release",
    ]