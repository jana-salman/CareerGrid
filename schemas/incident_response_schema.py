from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IncidentResponse(BaseModel):
    task_type: Literal["incident_investigation"]

    incident_id: Literal["INC-2048"]

    selected_root_cause: Literal[
        "missing_product_id"
    ]

    investigation_actions: list[
        Literal[
            "inspect_logs",
            "compare_payloads",
            "trace_code"
        ]
    ] = Field(
        min_length=3,
        max_length=3
    )

    diagnosis_attempts: int = Field(
        ge=1,
        le=100
    )

    incorrect_diagnosis_attempts: int = Field(
        ge=0,
        le=100
    )

    diagnostic_runs: int = Field(
        ge=1,
        le=100
    )

    selected_missing_field: Literal[
        "product_id"
    ]

    selected_failure_mechanism: Literal[
        "unsafe_dictionary_access"
    ]

    selected_current_status: Literal[
        500
    ]

    selected_expected_status: Literal[
        400
    ]

    selected_fix: Literal[
        "validate_product_id"
    ]

    hints_used: int = Field(
        ge=0,
        le=10
    )

    guided_diagnosis_used: bool = False

    diagnosis_confirmed: Literal[True]

    technical_finding: str = Field(
        min_length=20,
        max_length=1500
    )

    @model_validator(mode="after")
    def validate_attempt_counts(self):
        if (
            self.incorrect_diagnosis_attempts
            > self.diagnosis_attempts
        ):
            raise ValueError(
                "Incorrect attempts cannot exceed total diagnosis attempts."
            )

        if (
            self.diagnostic_runs
            != self.diagnosis_attempts
        ):
            raise ValueError(
                "Diagnostic runs must match diagnosis attempts."
            )

        return self