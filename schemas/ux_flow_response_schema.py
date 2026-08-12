from typing import Literal

from pydantic import BaseModel, Field


class UXFlowResponse(BaseModel):
    """Validated response for UX Designer Step 3."""

    task_type: Literal["ux_flow_builder"] = "ux_flow_builder"

    issue_id: Literal["UX-2048"] = "UX-2048"

    selected_flow: list[str] = Field(
        min_length=4,
        max_length=8,
    )

    removed_steps: list[str] = Field(
        default_factory=list
    )

    flow_test_runs: int = Field(
        ge=0,
        le=1000,
        default=0
    )

    hints_used: int = Field(
        ge=0,
        le=100,
        default=0
    )

    design_reasoning: str = Field(
        min_length=20,
        max_length=1500
    )