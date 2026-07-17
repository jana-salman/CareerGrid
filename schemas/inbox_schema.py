from typing import Literal

from pydantic import BaseModel, Field


class InboxEmail(BaseModel):
    """One email displayed in the simulated inbox."""

    id: str = Field(
        description="A unique identifier such as email_1."
    )

    sender_name: str = Field(
        description="The fictional name of the email sender."
    )

    sender_role: str = Field(
        description="The sender's workplace role."
    )

    subject: str = Field(
        description="A realistic workplace email subject."
    )

    body: str = Field(
        description="The complete email body."
    )

    timestamp: str = Field(
        description="A morning time in HH:MM format."
    )

    priority: Literal[
        "critical",
        "high",
        "medium",
        "low",
    ] = Field(
        description=(
            "The hidden priority used for evaluation. "
            "It must not be shown to the user."
        )
    )

    has_attachment: bool = Field(
        description="Whether the email contains an attachment."
    )

    attachment_name: str | None = Field(
        default=None,
        description=(
            "A fictional attachment filename, or null when "
            "there is no attachment."
        ),
    )

    linked_ticket_id: str | None = Field(
        default=None,
        description=(
            "The related bug ticket ID for the critical email, "
            "or null for unrelated emails."
        ),
    )


class InboxAnswerKey(BaseModel):
    """Hidden information used for scoring the task."""

    recommended_priority_order: list[str] = Field(
        description=(
            "Email IDs ordered from most urgent to least urgent."
        )
    )

    best_first_action: str = Field(
        description=(
            "The safest and most professional first action."
        )
    )

    explanation: str = Field(
        description=(
            "A brief explanation of why the urgent email "
            "requires immediate attention."
        )
    )


class BackendInboxTask(BaseModel):
    """Complete AI-generated Backend Developer inbox task."""

    task_type: Literal["inbox"] = "inbox"

    title: str = Field(
        description="A short title for the morning inbox task."
    )

    introduction: str = Field(
        description=(
            "A short introduction welcoming the user to their "
            "Backend Developer workday."
        )
    )

    company_name: str = Field(
        description="The company selected by the user."
    )

    position_name: Literal["Backend Developer"] = (
        "Backend Developer"
    )

    emails: list[InboxEmail] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Exactly five workplace emails. Exactly one must "
            "relate to the urgent production login incident."
        ),
    )

    available_first_actions: list[str] = Field(
        min_length=3,
        max_length=5,
        description=(
            "Actions the user can choose after reviewing "
            "the inbox."
        ),
    )

    reply_instruction: str = Field(
        description=(
            "An instruction asking the user to write a "
            "professional reply."
        )
    )

    answer_key: InboxAnswerKey = Field(
        description=(
            "Hidden information used later for scoring."
        )
    )