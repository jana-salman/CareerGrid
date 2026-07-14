import os
from typing import Literal

from google.genai import types
from pydantic import BaseModel, Field

from services.gemini_service import get_gemini_client


class InboxEmail(BaseModel):
    """
    Represents one email displayed in the simulated inbox.
    """

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

    priority: Literal["critical", "high", "medium", "low"] = Field(
        description=(
            "The hidden priority used by the backend for evaluation. "
            "It must not be shown directly to the user."
        )
    )

    has_attachment: bool = Field(
        description="Whether the email has an attachment."
    )

    attachment_name: str | None = Field(
        default=None,
        description=(
            "A fictional attachment filename, or null when there "
            "is no attachment."
        )
    )

    linked_ticket_id: str | None = Field(
        default=None,
        description=(
            "The related bug-ticket ID for the critical email, "
            "or null for unrelated emails."
        )
    )


class InboxAnswerKey(BaseModel):
    """
    Hidden evaluation information.

    This data must not be displayed in the HTML page.
    """

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
            "A brief explanation of why the critical email "
            "requires immediate attention."
        )
    )


class BackendInboxTask(BaseModel):
    """
    Complete AI-generated inbox task.
    """

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
        description="The company selected by the CareerGrid user."
    )

    position_name: Literal["Backend Developer"] = "Backend Developer"

    emails: list[InboxEmail] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Exactly five workplace emails. Exactly one must relate "
            "to the urgent production login incident."
        )
    )

    available_first_actions: list[str] = Field(
        min_length=3,
        max_length=5,
        description=(
            "Actions the user can choose after prioritizing the inbox."
        )
    )

    reply_instruction: str = Field(
        description=(
            "A short instruction asking the user to reply "
            "professionally to the relevant person."
        )
    )

    answer_key: InboxAnswerKey = Field(
        description=(
            "Hidden information used later for rule-based scoring."
        )
    )


def generate_backend_inbox_task(
    company_name: str = "CareerGrid Technologies"
) -> dict:
    """
    Generate the first interactive task for a Backend Developer.

    Args:
        company_name:
            The company selected by the user.

    Returns:
        A validated Python dictionary matching BackendInboxTask.

    Raises:
        RuntimeError:
            If Gemini returns no usable response.
    """

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite"
    )

    prompt = f"""
You are designing the first task of a realistic CareerGrid
workplace simulation.

Career:
Software Engineering

Position:
Junior Backend Developer

Company:
{company_name}

Main storyline:
A production login problem appeared shortly after a backend
deployment. Customers are unable to authenticate.

Generate an interactive morning inbox task.

Requirements:

1. Generate exactly five fictional workplace emails.
2. Exactly one email must report the urgent production login failure.
3. The critical email must link to a fictional bug ticket.
4. The other four emails must be realistic distractions or
   lower-priority workplace responsibilities.
5. Include a mixture of messages from roles such as:
   - Engineering Manager
   - QA Engineer
   - Human Resources
   - Product Manager
   - Backend Developer
   - Customer Support
6. Do not mention that this is a quiz.
7. Do not directly reveal which email the user should choose.
8. Keep the difficulty suitable for a junior Backend Developer.
9. Use fictional employee names.
10. Do not use real confidential company information.
11. The answer key must correctly identify the recommended priority.
12. The available actions must include both reasonable and
    less-effective choices.
13. The written content must be concise enough to display inside
    an email application interface.
"""

    with get_gemini_client() as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BackendInboxTask,
                temperature=0.7,
            ),
        )

    if response.parsed:
        generated_task = response.parsed

        if isinstance(generated_task, BackendInboxTask):
            return generated_task.model_dump()

        return BackendInboxTask.model_validate(
            generated_task
        ).model_dump()

    if response.text:
        return BackendInboxTask.model_validate_json(
            response.text
        ).model_dump()

    raise RuntimeError(
        "Gemini did not return an inbox simulation."
    )