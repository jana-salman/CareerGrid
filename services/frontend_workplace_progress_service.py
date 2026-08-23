"""Validate and normalize evidence from the five-step Frontend workflow."""

from copy import deepcopy
from typing import Any


class FrontendProgressValidationError(ValueError):
    """Raised when a Frontend step response violates the workflow contract."""


ALLOWED_COMMANDS = {
    "help",
    "clear",
    "npm test",
    "npm run lint",
    "npm run build",
    "git diff",
}
ALLOWED_FILES = {
    "index.html",
    "styles.css",
    "product.js",
    "product.test.js",
    "README.md",
}
STEP_FIELDS = {
    1: {
        "opened_email_ids",
        "selected_email_id",
        "selected_priority",
        "selected_action",
        "written_response",
    },
    2: {
        "pages_inspected",
        "viewports_tested",
        "evidence_opened",
        "selected_root_cause",
        "proposed_next_action",
        "investigation_summary",
    },
    3: {"files_opened", "changed_files", "fix_explanation"},
    4: {
        "commands_run",
        "tests_performed",
        "viewport_checks",
        "accessibility_checks",
        "release_decision",
    },
    5: {
        "reviewed_files",
        "commit_message",
        "pr_title",
        "pr_description",
        "testing_checklist",
        "release_recommendation",
        "final_team_message",
    },
}


def _strings(value: Any, *, maximum: int = 30) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise FrontendProgressValidationError("Expected a bounded list.")
    result = []
    for item in value:
        text = str(item).strip()
        if text and len(text) <= 200:
            result.append(text)
    return list(dict.fromkeys(result))


def _text(value: Any, *, required: bool = False, maximum: int = 3000) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise FrontendProgressValidationError("A required response is missing.")
    if len(text) > maximum:
        raise FrontendProgressValidationError("Response text is too long.")
    return text


def _patch_checks(changed_files: dict[str, str]) -> dict[str, bool]:
    script = changed_files.get("product.js", "")
    html = changed_files.get("index.html", "")
    uses_button = (
        "#buy-now-btn" in script
        or "getElementById('buy-now-btn')" in script
        or 'getElementById("buy-now-btn")' in script
    )
    wrong_selector = "#checkout-btn" in script
    ready = "DOMContentLoaded" in script or "defer" in html
    guard = "if (" in script and ("Button" in script or "button" in script)
    click = "addEventListener" in script and "click" in script
    semantic = not html or ("<button" in html and 'type="button"' in html)
    return {
        "correct_selector": uses_button and not wrong_selector,
        "safe_initialization": ready,
        "null_guard": guard,
        "click_handler": click,
        "semantic_button": semantic,
    }


def validate_frontend_progress(
    *,
    step: int,
    payload: dict[str, Any],
    existing_responses: dict[str, Any],
) -> dict[str, Any]:
    """Validate one step while enforcing sequential completion and safe input."""

    if step not in STEP_FIELDS or not isinstance(payload, dict):
        raise FrontendProgressValidationError("Invalid Frontend task response.")
    unknown = set(payload) - STEP_FIELDS[step]
    if unknown:
        raise FrontendProgressValidationError("Frontend response contains unsupported fields.")
    if step > 1 and not isinstance(
        existing_responses.get(f"step_{step - 1}"),
        dict,
    ):
        raise FrontendProgressValidationError("Complete the previous Frontend task first.")

    if step == 1:
        result = {
            "opened_email_ids": _strings(
                payload.get("opened_email_ids", []), maximum=5
            ),
            "selected_email_id": _text(
                payload.get("selected_email_id"), required=True, maximum=100
            ),
            "selected_priority": _text(
                payload.get("selected_priority"), required=True, maximum=30
            ),
            "selected_action": _text(
                payload.get("selected_action"), required=True, maximum=200
            ),
            "written_response": _text(
                payload.get("written_response"), required=True, maximum=1500
            ),
        }
    elif step == 2:
        result = {
            "pages_inspected": _strings(payload.get("pages_inspected", [])),
            "viewports_tested": _strings(
                payload.get("viewports_tested", []), maximum=3
            ),
            "evidence_opened": _strings(payload.get("evidence_opened", [])),
            "selected_root_cause": _text(
                payload.get("selected_root_cause"), required=True, maximum=200
            ),
            "proposed_next_action": _text(
                payload.get("proposed_next_action"), required=True, maximum=500
            ),
            "investigation_summary": _text(
                payload.get("investigation_summary"), required=True, maximum=1500
            ),
        }
    elif step == 3:
        changed = payload.get("changed_files")
        if not isinstance(changed, dict) or not changed or len(changed) > 4:
            raise FrontendProgressValidationError("Submit a focused changed-files patch.")
        normalized = {}
        for path, content in changed.items():
            if path not in ALLOWED_FILES:
                raise FrontendProgressValidationError(
                    "Patch contains an unrelated or unsafe file."
                )
            normalized[path] = _text(content, required=True, maximum=12_000)
        result = {
            "files_opened": _strings(payload.get("files_opened", [])),
            "changed_files": normalized,
            "fix_explanation": _text(
                payload.get("fix_explanation"), required=True, maximum=1500
            ),
            "patch_checks": _patch_checks(normalized),
        }
    elif step == 4:
        commands = _strings(payload.get("commands_run", []), maximum=20)
        if any(command not in ALLOWED_COMMANDS for command in commands):
            raise FrontendProgressValidationError("Terminal command is not allowed.")
        patch = existing_responses["step_3"].get("changed_files", {})
        checks = _patch_checks(patch)
        tests = {
            "desktop_mouse": checks["correct_selector"] and checks["click_handler"],
            "mobile_layout": checks["correct_selector"],
            "keyboard_activation": (
                checks["semantic_button"] and checks["click_handler"]
            ),
            "focus_visibility": True,
            "console_clean": all(
                checks[key]
                for key in ("correct_selector", "safe_initialization", "null_guard")
            ),
            "repeated_clicks": checks["click_handler"],
            "regression": checks["semantic_button"],
        }
        result = {
            "commands_run": commands,
            "tests_performed": _strings(payload.get("tests_performed", [])),
            "viewport_checks": _strings(
                payload.get("viewport_checks", []), maximum=3
            ),
            "accessibility_checks": _strings(payload.get("accessibility_checks", [])),
            "release_decision": _text(
                payload.get("release_decision"), required=True, maximum=50
            ),
            "verified_results": tests,
            "all_required_tests_passed": all(tests.values()),
        }
    else:
        prior_patch = existing_responses["step_3"].get("changed_files", {})
        reviewed = _strings(payload.get("reviewed_files", []), maximum=10)
        if not reviewed or set(reviewed) != set(prior_patch):
            raise FrontendProgressValidationError("Review the same files changed in Task 3.")
        result = {
            "reviewed_files": reviewed,
            "commit_message": _text(
                payload.get("commit_message"), required=True, maximum=200
            ),
            "pr_title": _text(
                payload.get("pr_title"), required=True, maximum=200
            ),
            "pr_description": _text(
                payload.get("pr_description"), required=True, maximum=3000
            ),
            "testing_checklist": _strings(payload.get("testing_checklist", [])),
            "release_recommendation": _text(
                payload.get("release_recommendation"), required=True, maximum=100
            ),
            "final_team_message": _text(
                payload.get("final_team_message"), required=True, maximum=3000
            ),
            "source_step_3_files": sorted(prior_patch),
            "source_step_4_results": deepcopy(
                existing_responses["step_4"].get("verified_results", {})
            ),
        }
    result.update({"task_type": "frontend_workplace", "step": step})
    return result
