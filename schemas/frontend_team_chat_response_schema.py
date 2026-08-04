from typing import Literal

from pydantic import BaseModel, Field, model_validator


FrontendChecklistItem = Literal[
    "root_cause_identified",
    "selector_fixed",
    "dom_ready_handled",
    "desktop_tested",
    "mobile_tested",
    "keyboard_tested",
]


class FrontendTeamChatRecipient(BaseModel):
    """The team lead receiving the frontend update."""

    id: Literal["frontend_team_lead"]
    name: Literal["Maya Lewis"]
    role: Literal["Frontend Team Lead"]


class FrontendTeamChatResponse(BaseModel):
    """Validated Step 5 frontend team-chat submission."""

    task_type: Literal["frontend_team_chat"]

    channel: Literal["frontend-releases"]

    recipient: FrontendTeamChatRecipient

    issue_id: Literal["FE-4021"]

    issue_status: Literal[
        "resolved",
        "needs_further_testing",
        "blocked",
    ]

    checklist: list[FrontendChecklistItem] = Field(
        min_length=6,
        max_length=6,
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

    accessibility_summary: str = Field(
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
            "selector_fixed",
            "dom_ready_handled",
            "desktop_tested",
            "mobile_tested",
            "keyboard_tested",
        }

        submitted_items = set(self.checklist)

        if submitted_items != required_items:
            raise ValueError(
                "Every required checklist item must be confirmed."
            )

        return self
    