from typing import Literal

from pydantic import BaseModel, Field

from schemas.inbox_schema import InboxAnswerKey, InboxEmail


class FrontendInboxTask(BaseModel):
    """Complete AI-generated Frontend Developer inbox task."""

    task_type: Literal["inbox"] = "inbox"

    title: str = Field(
        description="A short title for the morning inbox task."
    )

    introduction: str = Field(
        description=(
            "A short introduction welcoming the user to their "
            "Frontend Developer workday."
        )
    )

    company_name: str = Field(
        description="The company selected by the user."
    )

    position_name: Literal["Frontend Developer"] = (
        "Frontend Developer"
    )

    emails: list[InboxEmail] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Exactly five workplace emails. Exactly one must "
            "relate to the urgent Buy Now checkout production issue."
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