"""Generate and validate the Frontend Developer workplace scenario.

All workplace scenarios pass through the shared validator first. This module
then enforces only the five-step workflow, email, UI metadata, and file rules
that are specific to the Frontend Developer experience.
"""

import json
import logging
import os
import re
from copy import deepcopy
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client
from services.scenario_generation_service import (
    ScenarioGenerationError,
    validate_workplace_scenario,
)


logger = logging.getLogger(__name__)

FRONTEND_SCENARIO_KIND = "frontend_workplace"
FRONTEND_ISSUE_ID = "FE-4021"
FRONTEND_TASK_COUNT = 5
FRONTEND_BACKGROUND_EMAIL_COUNT = 4
FRONTEND_INBOX_EMAIL_COUNT = 5
FRONTEND_MIN_PROJECT_FILES = 4
FRONTEND_MAX_PROJECT_FILES = 10

FRONTEND_APPLICATIONS = ("mail", "browser", "vscode", "testing", "github")
FRONTEND_FILE_EXTENSIONS = (".html", ".css", ".js", ".json", ".md")
FRONTEND_REQUIRED_FILES = {"index.html", "styles.css", "product.js", "package.json"}
FRONTEND_TERMINAL_COMMANDS = {
    "help",
    "clear",
    "npm test",
    "npm run lint",
    "npm run build",
    "git diff",
}
FRONTEND_EMAIL_PRIORITIES = {"critical", "high", "medium", "low"}
FIREBASE_FORBIDDEN_KEY_CHARACTERS = {".", "#", "$", "/", "[", "]"}
FORBIDDEN_FRONTEND_COMMANDS = re.compile(
    r"\b(?:rm\s+-rf|curl|wget|powershell|sudo)\b",
    re.IGNORECASE,
)


def _email(
    email_id: str,
    sender: str,
    title: str,
    subject: str,
    body: str,
    priority: str,
    ticket: str | None = None,
) -> dict[str, Any]:
    """Build one fictional inbox message in the established public shape."""

    return {
        "id": email_id,
        "sender_name": sender,
        "sender_title": title,
        "sender_email": f"{email_id}@careergrid.example",
        "subject": subject,
        "body": body,
        "priority": priority,
        "linked_ticket_id": ticket,
    }


def deterministic_frontend_scenario(company_name: str, attempt_id: str) -> dict:
    """Return the validated fictional fallback used when generation fails."""

    urgent = _email(
        "buy-now-incident",
        "Maya Lewis",
        "Frontend Team Lead",
        "Urgent: Buy Now no longer opens checkout",
        (
            "QA confirmed that the product-page Buy Now interaction stopped "
            "opening the checkout panel after today's deployment. Reproduce it "
            "on desktop and mobile, investigate the frontend evidence, and "
            "prepare a focused fix for review."
        ),
        "critical",
        FRONTEND_ISSUE_ID,
    )
    background = [
        _email(
            "qa-followup",
            "Noah Reed",
            "QA Engineer",
            "Mobile regression notes",
            "I added viewport details to the frontend ticket for later review.",
            "high",
        ),
        _email(
            "ux-copy",
            "Priya Shah",
            "UX Designer",
            "Checkout copy review",
            "Could we review the checkout helper text later this week?",
            "medium",
        ),
        _email(
            "roadmap",
            "Elena Park",
            "Product Manager",
            "Next sprint refinement",
            "Tomorrow's refinement agenda is ready; no action is needed today.",
            "low",
        ),
        _email(
            "benefits",
            "Jordan Bell",
            "People Operations",
            "Benefits reminder",
            "The optional benefits session is next Friday.",
            "low",
        ),
    ]
    files = [
        {
            "path": "index.html",
            "content": """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="styles.css"><script src="product.js" defer></script></head><body><main><article class="product"><h1>Everyday Headphones</h1><button id="buy-now-btn" class="buy-now" type="button">Buy Now</button><section id="checkout-panel" class="checkout" hidden aria-live="polite">Checkout ready</section></article></main></body></html>""",
        },
        {
            "path": "styles.css",
            "content": """body { margin: 0; font: 16px system-ui; background: #071126; color: white; }
.product { width: min(680px, calc(100% - 32px)); margin: 48px auto; }
.buy-now { min-height: 44px; padding: 10px 18px; }
.buy-now:focus-visible { outline: 3px solid #69c9ff; outline-offset: 3px; }
@media (max-width: 480px) { .product { margin-top: 20px; } .buy-now { width: 100%; } }""",
        },
        {
            "path": "product.js",
            "content": """const checkoutButton = document.querySelector('#checkout-btn');
const checkoutPanel = document.querySelector('#checkout-panel');

function openCheckoutPanel() {
    checkoutPanel.hidden = false;
}

checkoutButton.addEventListener('click', openCheckoutPanel);""",
        },
        {
            "path": "product.test.js",
            "content": (
                "// Controlled CareerGrid checks cover mouse, keyboard, repeated "
                "activation, and mobile layout."
            ),
        },
        {
            "path": "package.json",
            "content": json.dumps(
                {
                    "name": "product-page",
                    "private": True,
                    "scripts": {
                        "test": "careergrid-test",
                        "lint": "careergrid-lint",
                        "build": "careergrid-build",
                    },
                },
                indent=2,
            ),
        },
        {
            "path": "README.md",
            "content": (
                "Run npm test, npm run lint, and npm run build in the simulated "
                "terminal. No external packages are required."
            ),
        },
    ]
    tasks = [
        {
            "step": 1,
            "application": "mail",
            "title": "Prioritize the production issue",
            "instructions": (
                "Review exactly five emails, prioritize the incident, choose a "
                "first action, and reply professionally."
            ),
            "required_actions": ["open_emails", "set_priority", "reply"],
        },
        {
            "step": 2,
            "application": "browser",
            "title": "Reproduce and investigate",
            "instructions": (
                "Test desktop, tablet, and mobile; inspect Elements, Console, "
                "Network, and listener evidence; record a diagnosis."
            ),
            "required_actions": [
                "test_viewports",
                "inspect_evidence",
                "submit_diagnosis",
            ],
        },
        {
            "step": 3,
            "application": "vscode",
            "title": "Implement a focused fix",
            "instructions": (
                "Inspect the project, edit only relevant frontend files, save, "
                "review the diff, and explain the change."
            ),
            "required_actions": ["open_files", "edit_code", "save_diff"],
        },
        {
            "step": 4,
            "application": "testing",
            "title": "Verify the fix",
            "instructions": (
                "Run controlled tests and verify mouse, mobile, keyboard, focus, "
                "console, repeat-click, and regression behavior."
            ),
            "required_actions": [
                "run_commands",
                "test_browser",
                "release_decision",
            ],
        },
        {
            "step": 5,
            "application": "github",
            "title": "Prepare the pull request",
            "instructions": (
                "Review the same diff and test evidence, create a simulated pull "
                "request, and send the final release update."
            ),
            "required_actions": ["review_diff", "create_pr", "final_update"],
        },
    ]
    public = {
        "scenario_id": f"frontend-{attempt_id}",
        "scenario_kind": FRONTEND_SCENARIO_KIND,
        "issue_id": FRONTEND_ISSUE_ID,
        "title": "Product-page Buy Now regression",
        "company_name": company_name,
        "fictional_company_notice": (
            "All employees, code, incidents, and messages in this simulation "
            "are fictional."
        ),
        "advisor": {
            "name": "Maya Lewis",
            "title": "Frontend Team Lead",
            "email": "maya.lewis@careergrid.example",
        },
        "task": {
            "id": FRONTEND_ISSUE_ID,
            "subject": urgent["subject"],
            "summary": urgent["body"],
            "body": urgent["body"],
            "priority": "high",
            "deadline_minutes": 240,
            "attachments": ["README.md"],
        },
        "background_emails": background,
        "inbox_emails": [urgent, *background],
        "project": {
            "display_name": "Product Page",
            "name": "product-page",
            "archive_name": "product-page.zip",
            "default_branch": "main",
            "files": files,
        },
        "resources": [
            {
                "id": "console-log",
                "name": "browser-console.log",
                "type": "text",
                "content": (
                    "Uncaught TypeError: Cannot read properties of null (reading "
                    "'addEventListener') at product.js"
                ),
            },
            {
                "id": "network-log",
                "name": "network.log",
                "type": "text",
                "content": (
                    "GET /product/headphones 200\n"
                    "GET /product.js 200\n"
                    "GET /styles.css 200"
                ),
            },
        ],
        "skill_targets": [
            "prioritization",
            "browser debugging",
            "semantic HTML",
            "responsive CSS",
            "DOM events",
            "accessibility",
            "testing",
            "Git workflow",
            "release communication",
        ],
        "frontend_tasks": tasks,
        "allowed_terminal_commands": [
            "help",
            "clear",
            "npm test",
            "npm run lint",
            "npm run build",
            "git diff",
        ],
        "viewport_presets": {"desktop": 1440, "tablet": 768, "mobile": 375},
    }
    private = {
        "root_cause": (
            "product.js queries #checkout-btn while the semantic button uses "
            "#buy-now-btn, leaving checkoutButton null."
        ),
        "expected_patch": {
            "product_js": (
                "Select #buy-now-btn after DOM readiness, guard missing elements, "
                "and retain native button keyboard behavior."
            )
        },
        "acceptable_alternatives": [
            "getElementById('buy-now-btn')",
            "deferred script with a null guard",
            "DOMContentLoaded initialization with a null guard",
        ],
        "verification_expectations": [
            "desktop click",
            "375px mobile",
            "Enter and Space",
            "visible focus",
            "no console errors",
            "repeated clicks",
            "build and lint",
        ],
        "scoring_notes": {
            "difficulty": "junior",
            "scope": "focused frontend regression",
        },
    }

    return validate_frontend_workplace_scenario(
        {"public_scenario": public, "private_context": private}
    )


def _is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) for item in value)
    )


def _validate_frontend_private_context(
    private_context: dict[str, Any],
    file_paths: set[str],
) -> None:
    """Validate Frontend-only private fields while they remain server-side."""

    _ = file_paths
    expected_patch = private_context.get("expected_patch")
    if not isinstance(expected_patch, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in expected_patch.items()
    ):
        raise ScenarioGenerationError(
            "Frontend private context needs a string expected-patch mapping."
        )

    if any(
        not key
        or any(
            character in key
            for character in FIREBASE_FORBIDDEN_KEY_CHARACTERS
        )
        for key in expected_patch
    ):
        raise ScenarioGenerationError(
            "Expected-patch identifiers must be Firebase-safe keys."
        )

    scoring_notes = private_context.get("scoring_notes")
    if not isinstance(scoring_notes, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in scoring_notes.items()
    ):
        raise ScenarioGenerationError(
            "Frontend private context needs string scoring notes."
        )

    for field_name in ("acceptable_alternatives", "verification_expectations"):
        if not _is_string_list(private_context.get(field_name)):
            raise ScenarioGenerationError(
                f"Frontend private field '{field_name}' must contain only strings."
            )


def _validate_frontend_email(email: Any) -> None:
    if not isinstance(email, dict):
        raise ScenarioGenerationError("Every Frontend email must be an object.")

    for field_name in (
        "id",
        "sender_name",
        "sender_title",
        "sender_email",
        "subject",
        "body",
    ):
        if not isinstance(email.get(field_name), str):
            raise ScenarioGenerationError(
                f"Frontend email field '{field_name}' must be text."
            )

    if email.get("priority") not in FRONTEND_EMAIL_PRIORITIES:
        raise ScenarioGenerationError("Frontend email priority is invalid.")

    linked_ticket_id = email.get("linked_ticket_id")
    if linked_ticket_id is not None and not isinstance(linked_ticket_id, str):
        raise ScenarioGenerationError(
            "Frontend linked ticket IDs must be text when provided."
        )


def validate_frontend_requirements(
    scenario: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Enforce only the requirements unique to the Frontend workflow."""

    public = scenario["public_scenario"]

    if public.get("scenario_kind") != FRONTEND_SCENARIO_KIND:
        raise ScenarioGenerationError("Frontend scenario kind is invalid.")

    for field_name in ("issue_id", "company_name", "fictional_company_notice"):
        if not isinstance(public.get(field_name), str):
            raise ScenarioGenerationError(
                f"Frontend public field '{field_name}' must be text."
            )

    project = public["project"]
    files = project["files"]
    if not FRONTEND_MIN_PROJECT_FILES <= len(files) <= FRONTEND_MAX_PROJECT_FILES:
        raise ScenarioGenerationError(
            "Frontend projects must contain between 4 and 10 files."
        )

    file_paths = {file_item["path"] for file_item in files}
    if not FRONTEND_REQUIRED_FILES.issubset(file_paths):
        raise ScenarioGenerationError("Frontend project is missing required files.")
    if project.get("default_branch") != "main":
        raise ScenarioGenerationError("Frontend project default branch must be main.")

    background_emails = public.get("background_emails")
    inbox_emails = public.get("inbox_emails")
    if (
        not isinstance(background_emails, list)
        or len(background_emails) != FRONTEND_BACKGROUND_EMAIL_COUNT
    ):
        raise ScenarioGenerationError(
            "Frontend scenarios need exactly four background emails."
        )
    if (
        not isinstance(inbox_emails, list)
        or len(inbox_emails) != FRONTEND_INBOX_EMAIL_COUNT
    ):
        raise ScenarioGenerationError(
            "Frontend scenarios need exactly five inbox emails."
        )

    for email in [*background_emails, *inbox_emails]:
        _validate_frontend_email(email)

    email_ids = [email["id"] for email in inbox_emails]
    if len(set(email_ids)) != FRONTEND_INBOX_EMAIL_COUNT:
        raise ScenarioGenerationError("Frontend inbox email IDs must be unique.")

    critical_emails = [
        email for email in inbox_emails if email["priority"] == "critical"
    ]
    if (
        len(critical_emails) != 1
        or critical_emails[0].get("linked_ticket_id") != public["issue_id"]
    ):
        raise ScenarioGenerationError(
            "Exactly one critical email must reference the Frontend issue."
        )

    tasks = public.get("frontend_tasks")
    if not isinstance(tasks, list) or len(tasks) != FRONTEND_TASK_COUNT:
        raise ScenarioGenerationError("Frontend scenarios need exactly five tasks.")
    if [task.get("step") for task in tasks if isinstance(task, dict)] != list(
        range(1, FRONTEND_TASK_COUNT + 1)
    ):
        raise ScenarioGenerationError(
            "Frontend tasks must contain ordered steps 1 through 5."
        )

    for task in tasks:
        if (
            not isinstance(task, dict)
            or task.get("application") not in FRONTEND_APPLICATIONS
        ):
            raise ScenarioGenerationError(
                "Frontend task application is invalid."
            )
        if not isinstance(task.get("title"), str) or not isinstance(
            task.get("instructions"), str
        ):
            raise ScenarioGenerationError(
                "Frontend task titles and instructions must be text."
            )
        if not _is_string_list(task.get("required_actions"), allow_empty=False):
            raise ScenarioGenerationError(
                "Every Frontend task needs at least one required action."
            )

    commands = public.get("allowed_terminal_commands")
    if not _is_string_list(commands) or any(
        command not in FRONTEND_TERMINAL_COMMANDS for command in commands
    ):
        raise ScenarioGenerationError(
            "Frontend scenario contains an unsupported terminal command."
        )

    viewports = public.get("viewport_presets")
    if not isinstance(viewports, dict) or not all(
        isinstance(name, str) and isinstance(width, int)
        for name, width in viewports.items()
    ):
        raise ScenarioGenerationError(
            "Frontend viewport presets must map names to integer widths."
        )

    if not _is_string_list(public.get("skill_targets")):
        raise ScenarioGenerationError(
            "Frontend skill targets must contain only text values."
        )

    public_text = json.dumps(public, ensure_ascii=False)
    if FORBIDDEN_FRONTEND_COMMANDS.search(public_text):
        raise ScenarioGenerationError(
            "Frontend scenario contains an unsafe command."
        )

    return scenario


def validate_frontend_workplace_scenario(
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Apply shared workplace checks followed by Frontend-only checks."""

    scenario = validate_workplace_scenario(
        payload,
        private_context_validator=_validate_frontend_private_context,
        allowed_extensions=FRONTEND_FILE_EXTENSIONS,
    )
    return validate_frontend_requirements(scenario)


def generate_frontend_workplace_scenario(
    *,
    company_name: str,
    attempt_id: str,
) -> tuple[dict, int]:
    """Generate a validated scenario, using the stable fallback on failure."""

    prompt = f"""Create a fictional Junior Frontend Developer CareerGrid scenario for display company {company_name!r}.
Use issue FE-4021 and one coherent Buy Now checkout-panel regression. Produce exactly five tasks: Mail prioritization,
Browser investigation, VS Code patch, Browser/Terminal verification, and GitHub/final communication. Use only HTML,
CSS, JavaScript, JSON, and Markdown. Do not reveal root_cause or expected_patch in public_scenario. Return JSON matching
the established Frontend workplace scenario structure. Attempt identifier: {attempt_id}."""

    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.45,
                ),
            )
        payload = json.loads(response.text or "")
        return validate_frontend_workplace_scenario(payload), 1
    except Exception as error:
        # Generation is intentionally fail-safe: the five-step simulation must
        # remain available when Gemini, JSON parsing, or validation is unavailable.
        logger.warning(
            "Frontend scenario generation failed; using deterministic fallback (%s).",
            type(error).__name__,
        )
        return deepcopy(deterministic_frontend_scenario(company_name, attempt_id)), 0
