from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FrontendInvestigationResponse(BaseModel):
    """Validated response from the Step 2 DevTools investigation."""

    task_type: Literal["frontend_investigation"]

    issue_id: Literal["FE-4021"]

    investigation_actions: list[
        Literal[
            "inspect_console",
            "compare_ids",
            "test_devices",
        ]
    ] = Field(
        min_length=3,
        max_length=3,
    )

    diagnosis_attempts: int = Field(
        ge=1,
        le=100,
    )

    incorrect_diagnosis_attempts: int = Field(
        ge=0,
        le=100,
    )

    diagnostic_runs: int = Field(
        ge=1,
        le=100,
    )

    selected_html_id: Literal["buy-now-btn"]

    selected_js_selector: Literal["#checkout-btn"]

    selected_root_cause: Literal["selector_id_mismatch"]

    selected_null_reason: Literal["element_not_found"]

    selected_failure_mechanism: Literal[
        "addeventlistener_on_null"
    ]

    hints_used: int = Field(
        ge=0,
        le=10,
    )

    guided_diagnosis_used: bool = False

    diagnosis_confirmed: Literal[True]

    technical_finding: str = Field(
        min_length=20,
        max_length=1500,
    )

    @model_validator(mode="after")
    def validate_attempt_counts(self):
        if (
            self.incorrect_diagnosis_attempts
            > self.diagnosis_attempts
        ):
            raise ValueError(
                "Incorrect attempts cannot exceed total "
                "diagnosis attempts."
            )

        if self.diagnostic_runs != self.diagnosis_attempts:
            raise ValueError(
                "Diagnostic runs must match diagnosis attempts."
            )

        return self