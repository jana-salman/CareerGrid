from typing import Literal

from pydantic import BaseModel, Field


class UXResearchResponse(BaseModel):
    """Validated response for UX Designer Step 2."""

    task_type: Literal["ux_research"] = "ux_research"

    issue_id: Literal["UX-2048"] = "UX-2048"

    opened_evidence: list[str] = Field(
        default_factory=list
    )

    selected_problem: str = Field(
        min_length=1,
        max_length=200
    )

    selected_evidence: list[str] = Field(
        default_factory=list
    )

    research_finding: str = Field(
        min_length=1,
        max_length=1500
    )

    investigation_attempts: int = Field(
        ge=0,
        le=1000,
        default=0
    )

    hints_used: int = Field(
        ge=0,
        le=100,
        default=0
    )