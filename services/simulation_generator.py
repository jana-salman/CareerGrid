import os
from google.genai import types
from schemas.inbox_schema import BackendInboxTask
from schemas.frontend_inbox_schema import FrontendInboxTask
from services.gemini_service import get_gemini_client



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


def generate_frontend_inbox_task(
    company_name: str = "CareerGrid Technologies"
) -> dict:
    """
    Generate the first interactive task for a Frontend Developer.

    Args:
        company_name:
            The company selected by the user.

    Returns:
        A validated Python dictionary matching FrontendInboxTask.

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
Junior Frontend Developer

Company:
{company_name}

Main storyline:
A recent product-page deployment caused the "Buy Now" button to
stop opening the checkout panel for some users, especially on
smaller screens. The button interaction fails in the browser.

Generate an interactive morning inbox task.

Requirements:

1. Generate exactly five fictional workplace emails.
2. Exactly one email must report the urgent "Buy Now" checkout
   production issue on the product page.
3. The critical email must link to a fictional bug ticket.
4. The other four emails must be realistic distractions or
   lower-priority workplace responsibilities.
5. Include a mixture of messages from roles such as:
   - Frontend Team Lead
   - QA Engineer
   - Product Manager
   - UX Designer
   - Customer Support
   - Human Resources
6. Do not mention that this is a quiz.
7. Do not directly reveal which email the user should choose.
8. Keep the difficulty suitable for a junior Frontend Developer.
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
                response_schema=FrontendInboxTask,
                temperature=0.7,
            ),
        )

    if response.parsed:
        generated_task = response.parsed

        if isinstance(generated_task, FrontendInboxTask):
            return generated_task.model_dump()

        return FrontendInboxTask.model_validate(
            generated_task
        ).model_dump()

    if response.text:
        return FrontendInboxTask.model_validate_json(
            response.text
        ).model_dump()

    raise RuntimeError(
        "Gemini did not return an inbox simulation."
    )