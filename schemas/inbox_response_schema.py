from typing import Literal

from pydantic import BaseModel, Field


class InboxResponse(BaseModel):
    """Validated response submitted for the inbox task."""

    task_type: Literal["inbox"]

    opened_emails: list[str] = Field(
        description="IDs of emails opened by the user."
    )

    priority_order: list[str] = Field(
        min_length=1,
        description=(
            "All email IDs ordered from highest to lowest priority."
        ),
    )

    selected_action: str = Field(
        min_length=1,
        max_length=500,
        description="The first action selected by the user.",
    )

    written_reply: str = Field(
        min_length=15,
        max_length=2000,
        description="The professional reply written by the user.",
    )