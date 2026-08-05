from typing import Literal, Optional

from pydantic import BaseModel, Field


class FrontendInvestigationResponse(BaseModel):
    """
    Validated response from the Step 2 DevTools investigation.

    The user is allowed to make mistakes. This schema records what
    the user selected and how they investigated; it does not force
    the correct answer. The final AI evaluation judges the quality.
    """

    task_type: Literal["frontend_investigation"]

    issue_id: Literal["FE-4021"]

    investigation_actions: list[str] = Field(
        default_factory=list,
    )

    diagnosis_attempts: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    incorrect_diagnosis_attempts: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    diagnostic_runs: int = Field(
        ge=0,
        le=1000,
        default=0,
    )

    selected_html_id: Optional[str] = None

    selected_js_selector: Optional[str] = None

    selected_root_cause: Optional[str] = None

    selected_null_reason: Optional[str] = None

    selected_failure_mechanism: Optional[str] = None

    hints_used: int = Field(
        ge=0,
        le=100,
        default=0,
    )

    guided_diagnosis_used: bool = False

    diagnosis_confirmed: bool = False

    technical_finding: str = Field(
        default="",
        max_length=1500,
    )