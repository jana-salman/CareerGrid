import os
from google.genai import types
from schemas.inbox_schema import BackendInboxTask
from schemas.frontend_inbox_schema import FrontendInboxTask
from schemas.ux_inbox_schema import UXInboxTask
from services.gemini_service import get_gemini_client
from schemas.data_analyst_inbox_schema import DataAnalystInboxTask



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

def generate_ux_inbox_task(
    company_name: str = "CareerGrid Technologies"
) -> dict:
    """
    Generate the first interactive task for a UX Designer.

    Args:
        company_name:
            The company selected by the user.

    Returns:
        A validated Python dictionary matching UXInboxTask.

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
UI/UX Design

Position:
Junior UX Designer

Company:
{company_name}

Main storyline:
The company's e-commerce checkout is experiencing a significant
increase in abandonment. Users are reaching checkout but many are
not completing their purchases.

Generate an interactive morning inbox task.

Requirements:

1. Generate exactly five fictional workplace emails.
2. Exactly one email must report the urgent checkout abandonment
   problem that requires UX investigation.
3. The critical email must link to a fictional UX issue or
   research ticket.
4. The other four emails must be realistic distractions or
   lower-priority workplace responsibilities.
5. Include a mixture of messages from roles such as:
   - Product Manager
   - UX Researcher
   - UI Designer
   - Frontend Developer
   - Customer Support
   - Marketing
   - Human Resources
6. Do not mention that this is a quiz.
7. Do not directly reveal which email the user should choose.
8. Keep the difficulty suitable for a junior UX Designer.
9. Use fictional employee names.
10. Do not use real confidential company information.
11. The answer key must correctly identify the recommended priority.
12. The available actions must include both reasonable and
    less-effective choices.
13. The written content must be concise enough to display inside
    an email application interface.
14. The urgent issue should naturally lead into a later user
    research investigation of the checkout experience.
"""

    with get_gemini_client() as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=UXInboxTask,
                temperature=0.7,
            ),
        )

    if response.parsed:
        generated_task = response.parsed

        if isinstance(generated_task, UXInboxTask):
            return generated_task.model_dump()

        return UXInboxTask.model_validate(
            generated_task
        ).model_dump()

    if response.text:
        return UXInboxTask.model_validate_json(
            response.text
        ).model_dump()

    raise RuntimeError(
        "Gemini did not return a UX inbox simulation."
    )

def generate_data_analyst_inbox_task(
    company_name: str = "InsightLab"
) -> dict:
    """
    Data Analyst - Step 1
    Interactive workplace inbox.
    """

    return {
        "task_type": "inbox",

        "title": "Data Analyst Workday Inbox",

        "introduction": (
            "You are starting your morning as a Data Analyst. "
            "Review the five messages, prioritize the work, "
            "choose what you would handle first, and write "
            "a professional response."
        ),

        "company_name": company_name,

        "position_name": "Data Analyst",

        "emails": [
            {
                "id": "revenue_discrepancy",
                "sender_name": "Olivia Carter",
                "sender_role": "Analytics Manager",
                "subject": "URGENT: Sales dashboard totals do not match Finance",
                "body": (
                    "Hi,\n\n"
                    "Leadership is reviewing the sales dashboard this "
                    "afternoon. The dashboard currently reports revenue "
                    "of $15,950, while Finance has verified $14,750.\n\n"
                    "Please investigate the underlying sales data before "
                    "the numbers are presented. We need to understand "
                    "whether this is a data-quality issue, transformation "
                    "problem, or reporting error.\n\n"
                    "Please prioritize this investigation and send me "
                    "an update when you identify the likely cause.\n\n"
                    "Thanks,\n"
                    "Olivia"
                ),
                "timestamp": "08:15",
                "priority": "critical",
                "has_attachment": True,
                "attachment_name": "sales_dashboard_summary.xlsx",
                "linked_ticket_id": "DA-2104",
            },

            {
                "id": "weekly_team_sync",
                "sender_name": "Marcus Thorne",
                "sender_role": "Analytics Manager",
                "subject": "Weekly analytics team sync moved",
                "body": (
                    "Hi team,\n\n"
                    "Our weekly analytics meeting has been moved to "
                    "tomorrow morning. No preparation is required today.\n\n"
                    "Thanks,\n"
                    "Marcus"
                ),
                "timestamp": "08:30",
                "priority": "low",
                "has_attachment": False,
                "attachment_name": None,
                "linked_ticket_id": None,
            },

            {
                "id": "marketing_report",
                "sender_name": "Elena Rodriguez",
                "sender_role": "Marketing Manager",
                "subject": "Request for ad-hoc campaign report",
                "body": (
                    "Hi,\n\n"
                    "Could you prepare last month's email campaign "
                    "click-through rates by the end of this week? "
                    "There is no urgency today.\n\n"
                    "Thanks,\n"
                    "Elena"
                ),
                "timestamp": "08:45",
                "priority": "medium",
                "has_attachment": False,
                "attachment_name": None,
                "linked_ticket_id": None,
            },

            {
                "id": "dashboard_color",
                "sender_name": "Daniel Kim",
                "sender_role": "Product Designer",
                "subject": "Dashboard chart color question",
                "body": (
                    "Hey,\n\n"
                    "When you have time, can you confirm which blue "
                    "we should use for the new dashboard chart? "
                    "This can wait until later.\n\n"
                    "Daniel"
                ),
                "timestamp": "09:00",
                "priority": "low",
                "has_attachment": True,
                "attachment_name": "dashboard_mockup.png",
                "linked_ticket_id": None,
            },

            {
                "id": "customer_export",
                "sender_name": "Sarah Jenkins",
                "sender_role": "Sales Operations Manager",
                "subject": "Customer export needed tomorrow",
                "body": (
                    "Hi,\n\n"
                    "Could you export the active-customer list for "
                    "tomorrow's sales planning session? We need it "
                    "before tomorrow morning.\n\n"
                    "Thanks,\n"
                    "Sarah"
                ),
                "timestamp": "09:10",
                "priority": "high",
                "has_attachment": False,
                "attachment_name": None,
                "linked_ticket_id": None,
            },
        ],

        "available_first_actions": [
            "Investigate the revenue dashboard discrepancy immediately",
            "Prepare the customer export first",
            "Start the marketing campaign report",
            "Answer the dashboard color question",
        ],

        "reply_instruction": (
            "Write a professional response to the person responsible "
            "for the task you chose to handle first."
        ),

        "answer_key": {
            "recommended_priority_order": [
                "revenue_discrepancy",
                "customer_export",
                "marketing_report",
                "weekly_team_sync",
                "dashboard_color",
            ],

            "best_first_action": (
                "Investigate the revenue dashboard discrepancy immediately"
            ),

            "explanation": (
                "The revenue discrepancy affects a leadership meeting "
                "later today and could cause incorrect financial "
                "information to be presented."
            ),
        },
    }

def generate_ui_inbox_task(company_name):
    """
    UI Designer - Step 1
    Interactive workplace inbox.

    Uses the same shared inbox structure as the existing
    Backend / Frontend / UX simulations.
    """

    return {
        "title": "UI Designer Workday Inbox",

        "introduction": (
            "You are starting your day as a UI Designer. "
            "Review the messages, prioritize the work, choose what "
            "you would handle first, and write a professional response."
        ),

        "position_name": "UI Designer",
        "company_name": company_name,

        "emails": [
            {
                "id": "ui_design_review",
                "sender_name": "Maya Chen",
                "sender_role": "Product Design Lead",
                "subject": "Dashboard visual design review needed before release",
                "preview": (
                    "The dashboard works, but the visual system needs "
                    "a final design review before release."
                ),
                "body": (
                    f"Hi,\n\n"
                    f"The engineering team at {company_name} has completed "
                    "the first implementation of our analytics dashboard.\n\n"
                    "Functionally it works, but the interface still has "
                    "visual inconsistencies across typography, spacing, "
                    "hierarchy, component styling, colors, states, and "
                    "alignment.\n\n"
                    "Please review the dashboard and identify the "
                    "highest-impact UI problems before engineering proceeds "
                    "with the final release.\n\n"
                    "Pay particular attention to visual hierarchy, "
                    "consistency, readability, spacing, component quality, "
                    "responsive behavior, and accessibility.\n\n"
                    "Please send me your recommendations and explain what "
                    "engineering should prioritize before release.\n\n"
                    "Thanks,\n"
                    "Maya"
                ),
                "priority": "high"
            },

            {
                "id": "ui_component_request",
                "sender_name": "Daniel Brooks",
                "sender_role": "Frontend Engineer",
                "subject": "Need clarification on button states",
                "preview": (
                    "Can you confirm the visual states for our buttons?"
                ),
                "body": (
                    "Hi,\n\n"
                    "I'm finishing the dashboard component implementation "
                    "and noticed that our buttons use inconsistent states "
                    "across the product.\n\n"
                    "Hover, focus, disabled, and loading states currently "
                    "look different depending on the screen.\n\n"
                    "Can you define which states should be standardized "
                    "before I finish implementation?\n\n"
                    "Thanks,\n"
                    "Daniel"
                ),
                "priority": "medium"
            },

            {
                "id": "ui_marketing_request",
                "sender_name": "Sofia Martinez",
                "sender_role": "Marketing Designer",
                "subject": "Quick color question for campaign graphic",
                "preview": (
                    "Which blue should I use for the campaign graphic?"
                ),
                "body": (
                    "Hey,\n\n"
                    "I'm preparing a campaign graphic and noticed two "
                    "similar blue colors in our design files.\n\n"
                    "Can you confirm which one should be used for the "
                    "primary CTA?\n\n"
                    "Thanks,\n"
                    "Sofia"
                ),
                "priority": "low"
            }
        ],

        # IMPORTANT:
        # inbox.html renders each action directly.
        # These MUST therefore be strings.
        "available_first_actions": [
            "Review the dashboard visual design issues before release",
            "Clarify the component states with the frontend engineer",
            "Answer the marketing color question",
            "Schedule a broader design review before taking action"
        ]
    }