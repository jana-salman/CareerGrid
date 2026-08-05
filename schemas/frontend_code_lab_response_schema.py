from typing import Literal

from pydantic import BaseModel, Field


class FrontendCodeLabResponse(BaseModel):
    """
    Validated response from the Frontend Code Lab.

    The user may submit code that does not pass every check. The
    server still analyzes the code and records which checks passed,
    but it does not block progress. The final AI evaluation scores
    the quality of the fix.
    """

    task_type: Literal["frontend_code_lab"]

    issue_id: Literal["FE-4021"]

    submitted_code: str = Field(
        min_length=1,
        max_length=5000,
    )

    test_runs: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    failed_test_runs: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    passed_tests: list[str] = Field(
        default_factory=list,
    )

    hints_used: int = Field(
        ge=0,
        le=100,
        default=0,
    )

    guided_fix_used: bool = False