"""Career, position, and company catalog queries."""

from services.simulation.backend_demo_scenario_service import (
    BACKEND_DEMO_COMPANY_NAME,
    is_backend_demo,
)

CAREER_DISPLAY_DATA = (
    {
        "id": "software-developer",
        "title": "Software Developer",
        "icon": "💻",
        "description": (
            "Practice problem-solving, debugging, and coding decisions."
        ),
    },
    {
        "id": "ui-ux-designer",
        "title": "UI/UX Designer",
        "icon": "🎨",
        "description": (
            "Explore user needs, design choices, and interface decisions."
        ),
    },
    {
        "id": "data-analyst",
        "title": "Data Analyst",
        "icon": "📊",
        "description": (
            "Analyze data, understand patterns, and make recommendations."
        ),
    },
)


POSITIONS_DATA = {
    "software-developer": {

        "backend-developer": {
            "title": "Backend Developer",
            "available": True,

            "companies": [
                {
                    "id": "technova",
                    "name": "TechNova",
                    "location": "Local"
                },

                {
                    "id": "brightsoft",
                    "name": "BrightSoft",
                    "location": "Global"
                }
            ]
        },

        "frontend-developer": {
            "title": "Frontend Developer",
            "available": True,

            "companies": [
                {
                    "id": "pixelworks",
                    "name": "PixelWorks",
                    "location": "Local"
                },

                {
                    "id": "cloudbyte",
                    "name": "CloudByte",
                    "location": "Global"
                }
            ]
        }
    },

    "ui-ux-designer": {

        "ux-designer": {
            "title": "UX Designer",
            "available": False,

            "companies": [
                {
                    "id": "designflow",
                    "name": "DesignFlow",
                    "location": "Local"
                },

                {
                    "id": "nexora",
                    "name": "Nexora",
                    "location": "Global"
                }
            ]
        },

        "ui-designer": {
            "title": "UI Designer",
            "available": False,

            "companies": [
                {
                    "id": "pixelcraft",
                    "name": "PixelCraft",
                    "location": "Local"
                },

                {
                    "id": "visionlabs",
                    "name": "VisionLabs",
                    "location": "Global"
                }
            ]
        }
    },

    "data-analyst": {

        "data-analyst": {
            "title": "Data Analyst",
            "available": False,

            "companies": [
                {
                    "id": "insightlab",
                    "name": "InsightLab",
                    "location": "Local"
                },

                {
                    "id": "datapulse",
                    "name": "DataPulse",
                    "location": "Global"
                }
            ]
        }
    }

}


def get_career_cards():
    """Return career cards with availability derived from their positions."""

    return [
        {
            **career,
            "available": any(
                position.get("available", False)
                for position in POSITIONS_DATA.get(career["id"], {}).values()
            ),
        }
        for career in CAREER_DISPLAY_DATA
    ]


def get_career_display_name(career_id: str) -> str:
    """Return the catalog title for a career identifier."""

    for career in CAREER_DISPLAY_DATA:
        if career.get("id") == career_id:
            return career.get("title", "Career")

    if career_id:
        return str(career_id).replace("-", " ").title()
    return "Career"


def get_position_title(career_id: str, position_id: str) -> str:
    """Return the catalog title for a position identifier."""

    title = POSITIONS_DATA.get(career_id, {}).get(position_id, {}).get("title")
    if title:
        return title
    if position_id:
        return str(position_id).replace("-", " ").title()
    return "Simulation"


def is_position_available(career_id, position_id):
    """Return whether a position has a working workplace workflow."""

    return bool(
        POSITIONS_DATA.get(career_id, {})
        .get(position_id, {})
        .get("available", False)
    )


def get_company_display_name(career_id, position_id, company_id):
    """Resolve a stable user-facing company name for all attempt pages."""

    if is_backend_demo(career_id, position_id, company_id):
        return BACKEND_DEMO_COMPANY_NAME

    position = POSITIONS_DATA.get(career_id, {}).get(position_id, {})

    for company in position.get("companies", []):
        if company.get("id") == company_id:
            return company.get("name", company_id)

    if company_id:
        return company_id.replace("-", " ").title()

    return "Company"


# Role profiles for CareerGrid's fictional practice companies. They give task
# generation the same kind of context a real job listing would, without
# claiming to describe a real employer.
COMPANY_ROLE_CONTEXT = {
    ("backend-developer", "technova"): {
        "title": "Junior Backend Developer",
        "company": "TechNova",
        "description": (
            "TechNova builds internal platforms for a mid-sized software company: user "
            "accounts, permissions, notifications, and reporting services used by other "
            "teams. Junior backend developers fix production issues in Python/Flask "
            "services, extend REST endpoints, keep API contracts stable for internal "
            "consumers, and write pytest regression tests. Work arrives as support "
            "escalations, tickets, and log excerpts, and changes are reviewed by senior "
            "engineers before release."
        ),
    },
    ("backend-developer", "brightsoft"): {
        "title": "Junior Backend Developer",
        "company": "BrightSoft",
        "description": (
            "BrightSoft runs a commerce platform for partner merchants: orders, payments, "
            "vouchers, inventory, and partner integrations exposed through JSON APIs. "
            "Junior backend developers implement business rules, validate partner input, "
            "make request handling safe to retry, handle data imports, and add unit and "
            "integration tests. They read API contracts and partner tickets and document "
            "rollout risks in handovers."
        ),
    },
    ("frontend-developer", "pixelworks"): {
        "title": "Junior Frontend Developer",
        "company": "PixelWorks",
        "description": (
            "PixelWorks designs and builds customer-facing web experiences for retail and "
            "media clients. Junior frontend developers implement and fix interactive UI in "
            "HTML, CSS, and vanilla JavaScript, work from design specs and QA reports, "
            "care about accessibility (keyboard use, focus, ARIA) and responsive layouts, "
            "and write unit tests for UI logic."
        ),
    },
    ("frontend-developer", "cloudbyte"): {
        "title": "Junior Frontend Developer",
        "company": "CloudByte",
        "description": (
            "CloudByte sells a cloud dashboard for small businesses: usage charts, billing "
            "settings, team management, and onboarding flows. Junior frontend developers "
            "build forms with validation, data tables with filtering and empty states, and "
            "settings pages, following product acceptance criteria and accessibility "
            "guidelines, with unit tests for client-side logic."
        ),
    },
}


def get_company_role_context(position_id: str, company_id: str) -> dict | None:
    """Return the defined role profile for a CareerGrid practice company."""

    context = COMPANY_ROLE_CONTEXT.get((position_id, company_id))
    return dict(context) if context else None
