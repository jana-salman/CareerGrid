"""Generate and validate the Frontend Developer workplace scenario.

All workplace scenarios pass through the shared validator first. This module
then enforces only the five-step workflow, email, UI metadata, and file rules
that are specific to the Frontend Developer experience.
"""

import json
import logging
import re
from copy import deepcopy
from typing import Any


from ai_prompt.prompts.scenario_v5 import build_frontend_prompt_v5
from ai_prompt.prompts.scenario_v4 import build_spec_prompt
from ai_prompt.rubrics.workplace_v1 import build_frontend_demo_private_rubric
from constants import WORKPLACE_FINAL_STEP
from services.ai.scenario_quality import assignment_quality_problems
from services.simulation.frontend_fallback_project import FALLBACK_FILES, FALLBACK_RESOURCES
from services.ai.generation_runtime import GenerationReport
from services.ai.scenario_drafts import (
    FRONTEND_BUILD_SCHEMA,
    FRONTEND_DRAFT_SCHEMA,
    FRONTEND_SPEC_SCHEMA,
    assemble_frontend,
)
from services.ai.scenario_generation_service import (
    ScenarioGenerationError,
    ScenarioQualityError,
    run_task_generation,
    assert_private_not_public,
    validate_task_brief,
    validate_workplace_scenario,
)


logger = logging.getLogger(__name__)

FRONTEND_SCENARIO_KIND = "frontend_workplace"
FRONTEND_ISSUE_ID = "FE-4021"
FRONTEND_TASK_COUNT = WORKPLACE_FINAL_STEP
FRONTEND_BACKGROUND_EMAIL_COUNT = 4
FRONTEND_INBOX_EMAIL_COUNT = 5
FRONTEND_MIN_PROJECT_FILES = 4
FRONTEND_MAX_PROJECT_FILES = 10

FRONTEND_APPLICATIONS = ("mail", "browser", "vscode", "testing", "github")
FRONTEND_FILE_EXTENSIONS = (".html", ".css", ".js", ".json", ".md")
FRONTEND_REQUIRED_FILES = {"index.html", "styles.css", "package.json"}
PATCH_CHECK_CATEGORIES = {"correctness", "robustness", "accessibility", "regression"}
PATCH_CHECK_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
MAX_PATCH_PATTERN_LENGTH = 200
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
            "QA confirmed that Buy Now stopped opening the checkout panel after "
            "today's deployment, and colour changes no longer update price or "
            "stock. Release is blocked. While you are in this code, please also "
            "close the open checkout issues in qa-regression-notes.md (quantity "
            "validation, duplicate summary lines, and focus when the panel opens). "
            "Start from browser-console.log, check the agreed behaviour in "
            "checkout-acceptance.md and the README, keep the existing styling and "
            "mobile layout, and add unit tests for any new logic. Reproduce on "
            "desktop and mobile, then deliver for review."
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
    files = deepcopy(FALLBACK_FILES)
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
            "title": "Deliver for review (pull request or main)",
            "instructions": (
                "Review the same diff and check results, then deliver through a "
                "pull request or by pushing to main, and send the final release update."
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
            "Practice simulation (fallback scenario): all employees, code, "
            "incidents, and messages are fictional. This is not a real "
            "employer assignment."
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
            "attachments": ["README.md", "console-log", "qa-notes", "acceptance"],
            "requirements": [
                "Buy Now opens the checkout panel again by mouse and keyboard on desktop and mobile, and colour changes update price and stock.",
                "Quantity must be a whole number from 1 to the selected colour's stock; invalid, zero, negative, or decimal values show a message in #quantity-error and keep checkout closed.",
                "The checkout summary shows exactly one line for the current selection, even after repeated Buy Now presses.",
                "Opening the panel moves keyboard focus into it and Close returns focus to Buy Now, while existing styling, focus outlines, out-of-stock handling, and the mobile layout are preserved.",
            ],
            "deliverables": [
                "Saved code changes to the product page scripts",
                "Unit tests for new quantity or pricing logic in tests/cart.test.js",
                "Delivery through a pull request or a push to main, plus a final team update",
            ],
            "acceptance_criteria": [
                "No console errors on load; Buy Now opens checkout and Midnight disables Buy Now.",
                "Quantity 0, -2, 2.5, and 5 on Sand show a message and do not open checkout.",
                "Pressing Buy Now twice shows one summary line with the correct total.",
                "Focus moves into the panel on open and back to Buy Now on Close.",
            ],
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
        "resources": deepcopy(FALLBACK_RESOURCES),
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
    private = build_frontend_demo_private_rubric()

    return validate_frontend_workplace_scenario(
        {"public_scenario": public, "private_context": private}
    )


def _is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) for item in value)
    )


def _validate_patch_checks(checks: Any, file_paths: set[str]) -> None:
    if not isinstance(checks, list) or not 3 <= len(checks) <= 8:
        raise ScenarioGenerationError("Frontend scenarios need 3-8 patch checks.")
    seen = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ScenarioGenerationError("Every patch check must be an object.")
        check_id = check.get("id")
        if not isinstance(check_id, str) or not PATCH_CHECK_ID_PATTERN.fullmatch(check_id) or check_id in seen:
            raise ScenarioGenerationError("Patch check IDs must be unique snake_case keys.")
        seen.add(check_id)
        if check.get("category") not in PATCH_CHECK_CATEGORIES:
            raise ScenarioGenerationError("Patch check category is invalid.")
        for field_name in ("description", "feedback"):
            if not isinstance(check.get(field_name), str) or not check[field_name].strip():
                raise ScenarioGenerationError(f"Patch check '{field_name}' is required.")
        conditions = check.get("any_of")
        if not isinstance(conditions, list) or not conditions:
            raise ScenarioGenerationError("Patch checks need at least one condition.")
        for condition in conditions:
            if not isinstance(condition, dict) or condition.get("file") not in file_paths:
                raise ScenarioGenerationError("Patch check refers to a missing project file.")
            patterns = 0
            for key in ("must_include_all", "must_include_any", "must_not_include"):
                values = condition.get(key, [])
                if not isinstance(values, list) or not all(
                    isinstance(item, str) and item and len(item) <= MAX_PATCH_PATTERN_LENGTH
                    for item in values
                ):
                    raise ScenarioGenerationError("Patch check patterns must be short strings.")
                patterns += len(values)
            if not patterns:
                raise ScenarioGenerationError("Patch check conditions need a pattern.")
            if set(condition.get("must_include_all", [])) & set(condition.get("must_not_include", [])):
                raise ScenarioGenerationError("Patch check condition contradicts itself.")


def _starter_fails_a_correctness_check(scenario: dict[str, dict[str, Any]]) -> None:
    """A generated task must not already pass its own correctness checks."""

    from services.simulation.frontend_workplace_progress_service import evaluate_patch_checks

    checks = scenario["private_context"]["patch_checks"]
    files = {item["path"]: item["content"] for item in scenario["public_scenario"]["project"]["files"]}
    results = evaluate_patch_checks(checks, files)
    if all(results[check["id"]] for check in checks if check["category"] == "correctness"):
        raise ScenarioGenerationError("Starter files already pass every correctness check.")


def _validate_frontend_private_context(
    private_context: dict[str, Any],
    file_paths: set[str],
) -> None:
    """Validate Frontend-only private fields while they remain server-side."""

    _validate_patch_checks(private_context.get("patch_checks"), file_paths)
    keywords = private_context.get("root_cause_keywords")
    if not _is_string_list(keywords, allow_empty=False) or len(keywords) > 5:
        raise ScenarioGenerationError("Frontend private context needs 1-5 root-cause keywords.")
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
    if not FRONTEND_REQUIRED_FILES.issubset(file_paths) or not any(
        path.endswith(".js") and not path.endswith(".test.js") for path in file_paths
    ):
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
    validate_frontend_requirements(scenario)
    validate_task_brief(scenario["public_scenario"])
    assert_private_not_public(scenario["public_scenario"], scenario["private_context"])
    _starter_fails_a_correctness_check(scenario)
    problems = assignment_quality_problems(scenario, kind="frontend")
    if problems:
        raise ScenarioQualityError(problems)
    return scenario


def normalize_generated_private_keys(payload: Any) -> Any:
    """Make private mapping keys Firebase-safe (models often use file names).

    These keys are private labels such as "form.js"; only their characters are
    changed, never their meaning, so this is not a quality shortcut.
    """

    private = payload.get("private_context") if isinstance(payload, dict) else None
    if not isinstance(private, dict):
        return payload
    for field_name in ("expected_patch", "scoring_notes"):
        mapping = private.get(field_name)
        if isinstance(mapping, dict):
            private[field_name] = {
                re.sub(r"[.#$/\[\]]", "_", str(key)) or "item": (
                    value if isinstance(value, str)
                    else "; ".join(map(str, value)) if isinstance(value, list)
                    else json.dumps(value, ensure_ascii=False)
                )
                for key, value in mapping.items()
            }
    return payload


def generate_frontend_workplace_scenario(
    *,
    company_name: str,
    attempt_id: str,
    job_context: dict[str, Any] | None = None,
    report: GenerationReport | None = None,
) -> tuple[dict, int]:
    """Generate a validated assignment within a time budget, else the fallback.

    Returns ``(scenario, generation_count)``; a count of 0 marks the fallback.
    ``report`` records each attempt and why the fallback was used.
    """

    report = report if report is not None else GenerationReport()
    report.kind = "frontend"
    report.attempt_id = attempt_id
    report.job_context_source = (job_context or {}).get("source", "")

    def build_prompt(feedback):
        return build_frontend_prompt_v5(
            company_name=company_name,
            job_context=job_context,
            feedback=feedback,
        )

    def spec_prompt(feedback):
        return build_spec_prompt(
            kind="frontend",
            role="Frontend Developer",
            difficulty="junior",
            competencies=["UI debugging", "JavaScript", "accessibility", "responsive layout", "testing"],
            company_name=company_name,
            job_context=job_context,
            feedback=feedback,
        )

    scenario = run_task_generation(
        kind="frontend",
        report=report,
        single_prompt=build_prompt,
        single_schema=FRONTEND_DRAFT_SCHEMA,
        spec_prompt=spec_prompt,
        spec_schema=FRONTEND_SPEC_SCHEMA,
        build_schema=FRONTEND_BUILD_SCHEMA,
        assemble=lambda draft: assemble_frontend(draft, attempt_id=attempt_id, company_name=company_name),
        validate=validate_frontend_workplace_scenario,
    )
    if scenario is not None:
        return scenario, len(report.attempts)
    # Fail-safe: the five-step simulation stays available with a substantial,
    # validated built-in assignment rather than a shallow generated one.
    logger.warning("Using the built-in Frontend fallback assignment: %s", report.failure_reason)
    return deepcopy(deterministic_frontend_scenario(company_name, attempt_id)), 0
