from typing import Literal

from pydantic import BaseModel, Field


class CodeLabResponse(BaseModel):
    """Validated response from the Backend Code Lab."""

    task_type: Literal["code_lab"]
    issue_id: Literal["API-184"]

    submitted_code: str = Field(
        min_length=20,
        max_length=5000,
    )

    test_runs: int = Field(
        ge=1,
        le=100,
    )

    failed_test_runs: int = Field(
        ge=0,
        le=100,
    )

    passed_tests: list[str]

    hints_used: int = Field(
        ge=0,
        le=10,
    )

    guided_fix_used: bool = False