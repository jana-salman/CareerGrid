from typing import Literal

from pydantic import BaseModel, Field


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
    """
    Validated Step 5 frontend team-chat submission.

    The user may send an incomplete or imperfect update. The
    checklist may be partially confirmed and the summaries may be
    short. Nothing is forced to be correct; the final AI evaluation
    judges the professionalism and completeness of the update.
    """

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
        default_factory=list,
        max_length=6,
    )

    root_cause: str = Field(
        default="",
        max_length=500,
    )

    fix_summary: str = Field(
        default="",
        max_length=500,
    )

    testing_summary: str = Field(
        default="",
        max_length=500,
    )

    accessibility_summary: str = Field(
        default="",
        max_length=500,
    )

    release_recommendation: Literal[
        "ready_for_review",
        "needs_more_testing",
        "do_not_release",
    ]

    message: str = Field(
        default="",
        max_length=3000,
    )

    preview_completed: bool = False

    all_required_items_confirmed: bool = False