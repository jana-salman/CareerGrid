import json
import re
from copy import deepcopy

from google.genai import types
from pydantic import ValidationError

from schemas.frontend_workplace_scenario_schema import FrontendWorkplaceScenario
from services.gemini_service import get_gemini_client


PRIVATE_KEYS = {"root_cause", "expected_patch", "scoring_notes", "private_context"}
FORBIDDEN_COMMANDS = re.compile(r"\b(?:rm\s+-rf|curl|wget|powershell|sudo)\b", re.IGNORECASE)


def _email(email_id, sender, title, subject, body, priority, ticket=None):
    return {
        "id": email_id, "sender_name": sender, "sender_title": title,
        "sender_email": f"{email_id}@careergrid.example", "subject": subject,
        "body": body, "priority": priority, "linked_ticket_id": ticket,
    }


def deterministic_frontend_scenario(company_name: str, attempt_id: str) -> dict:
    """Return a complete fictional scenario when AI generation is unavailable."""
    issue_id = "FE-4021"
    urgent = _email(
        "buy-now-incident", "Maya Lewis", "Frontend Team Lead",
        "Urgent: Buy Now no longer opens checkout",
        "QA confirmed that the product-page Buy Now interaction stopped opening the checkout panel after today's deployment. Reproduce it on desktop and mobile, investigate the frontend evidence, and prepare a focused fix for review.",
        "critical", issue_id,
    )
    background = [
        _email("qa-followup", "Noah Reed", "QA Engineer", "Mobile regression notes", "I added viewport details to the frontend ticket for later review.", "high"),
        _email("ux-copy", "Priya Shah", "UX Designer", "Checkout copy review", "Could we review the checkout helper text later this week?", "medium"),
        _email("roadmap", "Elena Park", "Product Manager", "Next sprint refinement", "Tomorrow's refinement agenda is ready; no action is needed today.", "low"),
        _email("benefits", "Jordan Bell", "People Operations", "Benefits reminder", "The optional benefits session is next Friday.", "low"),
    ]
    files = [
        {"path": "index.html", "content": """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><link rel=\"stylesheet\" href=\"styles.css\"><script src=\"product.js\" defer></script></head><body><main><article class=\"product\"><h1>Everyday Headphones</h1><button id=\"buy-now-btn\" class=\"buy-now\" type=\"button\">Buy Now</button><section id=\"checkout-panel\" class=\"checkout\" hidden aria-live=\"polite\">Checkout ready</section></article></main></body></html>"""},
        {"path": "styles.css", "content": """body { margin: 0; font: 16px system-ui; background: #071126; color: white; }
.product { width: min(680px, calc(100% - 32px)); margin: 48px auto; }
.buy-now { min-height: 44px; padding: 10px 18px; }
.buy-now:focus-visible { outline: 3px solid #69c9ff; outline-offset: 3px; }
@media (max-width: 480px) { .product { margin-top: 20px; } .buy-now { width: 100%; } }"""},
        {"path": "product.js", "content": """const checkoutButton = document.querySelector('#checkout-btn');
const checkoutPanel = document.querySelector('#checkout-panel');

function openCheckoutPanel() {
    checkoutPanel.hidden = false;
}

checkoutButton.addEventListener('click', openCheckoutPanel);"""},
        {"path": "product.test.js", "content": """// Controlled CareerGrid checks cover mouse, keyboard, repeated activation, and mobile layout."""},
        {"path": "package.json", "content": json.dumps({"name": "product-page", "private": True, "scripts": {"test": "careergrid-test", "lint": "careergrid-lint", "build": "careergrid-build"}}, indent=2)},
        {"path": "README.md", "content": "Run npm test, npm run lint, and npm run build in the simulated terminal. No external packages are required."},
    ]
    tasks = [
        {"step": 1, "application": "mail", "title": "Prioritize the production issue", "instructions": "Review exactly five emails, prioritize the incident, choose a first action, and reply professionally.", "required_actions": ["open_emails", "set_priority", "reply"]},
        {"step": 2, "application": "browser", "title": "Reproduce and investigate", "instructions": "Test desktop, tablet, and mobile; inspect Elements, Console, Network, and listener evidence; record a diagnosis.", "required_actions": ["test_viewports", "inspect_evidence", "submit_diagnosis"]},
        {"step": 3, "application": "vscode", "title": "Implement a focused fix", "instructions": "Inspect the project, edit only relevant frontend files, save, review the diff, and explain the change.", "required_actions": ["open_files", "edit_code", "save_diff"]},
        {"step": 4, "application": "testing", "title": "Verify the fix", "instructions": "Run controlled tests and verify mouse, mobile, keyboard, focus, console, repeat-click, and regression behavior.", "required_actions": ["run_commands", "test_browser", "release_decision"]},
        {"step": 5, "application": "github", "title": "Prepare the pull request", "instructions": "Review the same diff and test evidence, create a simulated pull request, and send the final release update.", "required_actions": ["review_diff", "create_pr", "final_update"]},
    ]
    public = {
        "scenario_id": f"frontend-{attempt_id}", "scenario_kind": "frontend_workplace",
        "issue_id": issue_id, "title": "Product-page Buy Now regression", "company_name": company_name,
        "fictional_company_notice": "All employees, code, incidents, and messages in this simulation are fictional.",
        "advisor": {"name": "Maya Lewis", "title": "Frontend Team Lead", "email": "maya.lewis@careergrid.example"},
        "task": {"id": issue_id, "subject": urgent["subject"], "summary": urgent["body"], "body": urgent["body"], "priority": "high", "deadline_minutes": 240, "attachments": ["README.md"]},
        "background_emails": background, "inbox_emails": [urgent, *background],
        "project": {"display_name": "Product Page", "name": "product-page", "archive_name": "product-page.zip", "default_branch": "main", "files": files},
        "resources": [
            {"id": "console-log", "name": "browser-console.log", "type": "text", "content": "Uncaught TypeError: Cannot read properties of null (reading 'addEventListener') at product.js"},
            {"id": "network-log", "name": "network.log", "type": "text", "content": "GET /product/headphones 200\nGET /product.js 200\nGET /styles.css 200"},
        ],
        "skill_targets": ["prioritization", "browser debugging", "semantic HTML", "responsive CSS", "DOM events", "accessibility", "testing", "Git workflow", "release communication"],
        "frontend_tasks": tasks,
        "allowed_terminal_commands": ["help", "clear", "npm test", "npm run lint", "npm run build", "git diff"],
        "viewport_presets": {"desktop": 1440, "tablet": 768, "mobile": 375},
    }
    private = {
        "root_cause": "product.js queries #checkout-btn while the semantic button uses #buy-now-btn, leaving checkoutButton null.",
        "expected_patch": {"product_js": "Select #buy-now-btn after DOM readiness, guard missing elements, and retain native button keyboard behavior."},
        "acceptable_alternatives": ["getElementById('buy-now-btn')", "deferred script with a null guard", "DOMContentLoaded initialization with a null guard"],
        "verification_expectations": ["desktop click", "375px mobile", "Enter and Space", "visible focus", "no console errors", "repeated clicks", "build and lint"],
        "scoring_notes": {"difficulty": "junior", "scope": "focused frontend regression"},
    }
    return FrontendWorkplaceScenario.model_validate({"public_scenario": public, "private_context": private}).model_dump()


def _contains_private_key(value) -> bool:
    if isinstance(value, dict):
        return any(key in PRIVATE_KEYS or _contains_private_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_private_key(child) for child in value)
    return False


def validate_frontend_workplace_scenario(payload: dict) -> dict:
    scenario = FrontendWorkplaceScenario.model_validate(payload).model_dump()
    if _contains_private_key(scenario["public_scenario"]):
        raise ValueError("Private evaluation data appeared in the public scenario.")
    public_text = json.dumps(scenario["public_scenario"], ensure_ascii=False)
    if FORBIDDEN_COMMANDS.search(public_text):
        raise ValueError("Frontend scenario contains an unsafe command.")
    return scenario


def generate_frontend_workplace_scenario(*, company_name: str, attempt_id: str) -> tuple[dict, int]:
    """Generate a structured scenario, falling back deterministically on any failure."""
    prompt = f"""Create a fictional Junior Frontend Developer CareerGrid scenario for display company {company_name!r}.
Use issue FE-4021 and one coherent Buy Now checkout-panel regression. Produce exactly five tasks: Mail prioritization,
Browser investigation, VS Code patch, Browser/Terminal verification, and GitHub/final communication. Use only HTML,
CSS, JavaScript, JSON, and Markdown. Do not reveal root_cause or expected_patch in public_scenario. Return JSON matching
the FrontendWorkplaceScenario schema. Attempt identifier: {attempt_id}."""
    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite", contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.45),
            )
        payload = json.loads(response.text or "")
        return validate_frontend_workplace_scenario(payload), 1
    except (Exception, ValidationError, ValueError, json.JSONDecodeError):
        return deepcopy(deterministic_frontend_scenario(company_name, attempt_id)), 0
