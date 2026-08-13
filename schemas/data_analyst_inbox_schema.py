from typing import Literal

from pydantic import BaseModel, Field

from schemas.inbox_schema import InboxAnswerKey, InboxEmail


class DataAnalystInboxTask(BaseModel):
    """Complete AI-generated Data Analyst inbox task."""

    task_type: Literal["inbox"] = "inbox"

    title: str = Field(
        description="A short title for the Data Analyst morning inbox task."
    )

    introduction: str = Field(
        description=(
            "A short introduction welcoming the user to their "
            "Data Analyst workday."
        )
    )

    company_name: str = Field(
        description="The company selected by the user."
    )

    position_name: Literal["Data Analyst"] = "Data Analyst"

    emails: list[InboxEmail] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Exactly five workplace emails. Exactly one must concern "
            "an urgent business reporting or data-quality problem."
        ),
    )

    available_first_actions: list[str] = Field(
        min_length=3,
        max_length=5,
        description=(
            "Actions the user can choose after reviewing the inbox."
        ),
    )

    reply_instruction: str = Field(
        description=(
            "An instruction asking the user to write a concise "
            "professional analyst reply."
        )
    )

    answer_key: InboxAnswerKey = Field(
        description="Hidden information used later for scoring."
    )