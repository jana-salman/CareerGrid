from typing import Literal

from pydantic import BaseModel, Field, model_validator


ChecklistItem = Literal[
    "root_cause_identified",
    "fix_implemented",
    "valid_payload_tested",
    "invalid_payload_tested",
    "server_error_prevented",
]


class TeamChatRecipient(BaseModel):
    """The team lead receiving the incident update."""

    id: Literal["backend_team_lead"]
    name: Literal["Alex Carter"]
    role: Literal["Backend Team Lead"]


class TeamChatResponse(BaseModel):
    """Validated Step 5 team-chat submission."""

    task_type: Literal["team_chat"]

    channel: Literal["backend-releases"]

    recipient: TeamChatRecipient

    incident_id: Literal["INC-2048"]

    incident_status: Literal[
        "resolved",
        "needs_further_testing",
        "blocked",
    ]

    checklist: list[ChecklistItem] = Field(
        min_length=5,
        max_length=5,
    )

    root_cause: str = Field(
        min_length=25,
        max_length=500,
    )

    fix_summary: str = Field(
        min_length=25,
        max_length=500,
    )

    testing_summary: str = Field(
        min_length=25,
        max_length=500,
    )

    release_recommendation: Literal[
        "ready_for_review",
        "needs_more_testing",
        "do_not_release",
    ]

    message: str = Field(
        min_length=100,
        max_length=3000,
    )

    preview_completed: Literal[True]

    all_required_items_confirmed: Literal[True]

    @model_validator(mode="after")
    def validate_complete_checklist(self):
        required_items = {
            "root_cause_identified",
            "fix_implemented",
            "valid_payload_tested",
            "invalid_payload_tested",
            "server_error_prevented",
        }

        submitted_items = set(
            self.checklist
        )

        if submitted_items != required_items:
            raise ValueError(
                "Every required checklist item must be confirmed."
            )

        return self