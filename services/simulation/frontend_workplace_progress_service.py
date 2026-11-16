"""Validate and normalize evidence from the five-step Frontend workflow."""

from copy import deepcopy
from typing import Any

from services.simulation.frontend_workplace_scenario_service import FRONTEND_TERMINAL_COMMANDS


class FrontendProgressValidationError(ValueError):
    """Raised when a Frontend step response violates the workflow contract."""


DELIVERY_MODES = {"pull_request", "main"}
LEGACY_ALLOWED_FILES = {
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
        "delivery_mode",
        "delivery_evidence",
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


def _condition_passes(condition: dict[str, Any], files: dict[str, str]) -> bool:
    content = files.get(condition.get("file", ""), "")
    if not content:
        return False
    include_all = condition.get("must_include_all") or []
    include_any = condition.get("must_include_any") or []
    exclude = condition.get("must_not_include") or []
    return (
        all(pattern in content for pattern in include_all)
        and (not include_any or any(pattern in content for pattern in include_any))
        and not any(pattern in content for pattern in exclude)
    )


def evaluate_patch_checks(
    checks: list[dict[str, Any]],
    files: dict[str, str],
) -> dict[str, bool]:
    """Run scenario-defined static checks against the final submitted files.

    These are deterministic text checks run by CareerGrid. They are recorded
    separately from any testing the participant describes in writing.
    """

    return {
        check["id"]: any(
            _condition_passes(condition, files) for condition in check.get("any_of", [])
        )
        for check in checks
    }


def _final_files(
    changed: dict[str, str],
    project_files: dict[str, str] | None,
) -> dict[str, str]:
    files = dict(project_files or {})
    files.update(changed)
    return files


def _delivery(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    mode = _text(payload.get("delivery_mode") or "pull_request", maximum=20)
    if mode not in DELIVERY_MODES:
        raise FrontendProgressValidationError(
            "Choose pull request or main as the delivery method."
        )
    raw = payload.get("delivery_evidence") or {}
    if not isinstance(raw, dict):
        raise FrontendProgressValidationError("Delivery evidence must be an object.")
    evidence = {
        "branch": _text(raw.get("branch"), maximum=120),
        "commit_id": _text(raw.get("commit_id"), maximum=60),
        "pull_request_url": _text(raw.get("pull_request_url"), maximum=300),
        "pushed": bool(raw.get("pushed")),
        "uncommitted_files": _strings(raw.get("uncommitted_files", []), maximum=30),
    }
    return mode, evidence


def validate_frontend_progress(
    *,
    step: int,
    payload: dict[str, Any],
    existing_responses: dict[str, Any],
    patch_checks: list[dict[str, Any]] | None = None,
    project_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate one step while enforcing sequential completion and safe input.

    Generated scenarios supply their own ``patch_checks`` and ``project_files``.
    Attempts created before that existed use the legacy Buy Now checks.
    """

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
        allowed = set(project_files or {}) or LEGACY_ALLOWED_FILES
        normalized = {}
        for path, content in changed.items():
            if path not in allowed:
                raise FrontendProgressValidationError(
                    "Patch contains an unrelated or unsafe file."
                )
            normalized[path] = _text(content, required=True, maximum=12_000)
        if patch_checks:
            if all(normalized[path] == str((project_files or {}).get(path, "")).strip() for path in normalized):
                raise FrontendProgressValidationError(
                    "No changes found. Edit and save the project files in VS Code first."
                )
            checks = evaluate_patch_checks(
                patch_checks, _final_files(normalized, project_files)
            )
        else:
            checks = _patch_checks(normalized)
        result = {
            "files_opened": _strings(payload.get("files_opened", [])),
            "changed_files": normalized,
            "fix_explanation": _text(
                payload.get("fix_explanation"), required=True, maximum=1500
            ),
            "patch_checks": checks,
        }
        if patch_checks:
            result["check_categories"] = {
                check["id"]: check.get("category", "correctness")
                for check in patch_checks
            }
    elif step == 4:
        commands = _strings(payload.get("commands_run", []), maximum=20)
        if any(command not in FRONTEND_TERMINAL_COMMANDS for command in commands):
            raise FrontendProgressValidationError("Terminal command is not allowed.")
        patch = existing_responses["step_3"].get("changed_files", {})
        if patch_checks:
            tests = evaluate_patch_checks(
                patch_checks, _final_files(patch, project_files)
            )
        else:
            tests = _legacy_verified_results(_patch_checks(patch))
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
            # Automated results come from CareerGrid's static checks; the lists
            # above are the participant's self-reported verification.
            "verified_results": tests,
            "verification_basis": "automated_static_checks",
            "all_required_tests_passed": all(tests.values()),
        }
    else:
        prior_patch = existing_responses["step_3"].get("changed_files", {})
        reviewed = _strings(payload.get("reviewed_files", []), maximum=10)
        if not reviewed or set(reviewed) != set(prior_patch):
            raise FrontendProgressValidationError("Review the same files changed in Task 3.")
        mode, delivery = _delivery(payload)
        if mode == "main" and not delivery["pushed"]:
            raise FrontendProgressValidationError(
                "Commit and push your work to main before delivering it."
            )
        requires_pr = mode == "pull_request"
        result = {
            "reviewed_files": reviewed,
            "commit_message": _text(
                payload.get("commit_message"), required=True, maximum=200
            ),
            "pr_title": _text(
                payload.get("pr_title"), required=requires_pr, maximum=200
            ),
            "pr_description": _text(
                payload.get("pr_description"), required=requires_pr, maximum=3000
            ),
            "testing_checklist": _strings(payload.get("testing_checklist", [])),
            "release_recommendation": _text(
                payload.get("release_recommendation"), required=True, maximum=100
            ),
            "final_team_message": _text(
                payload.get("final_team_message"), required=True, maximum=3000
            ),
            "delivery_mode": mode,
            "delivery_evidence": delivery,
            "source_step_3_files": sorted(prior_patch),
            "source_step_4_results": deepcopy(
                existing_responses["step_4"].get("verified_results", {})
            ),
        }
    result.update({"task_type": "frontend_workplace", "step": step})
    return result


def _legacy_verified_results(checks: dict[str, bool]) -> dict[str, bool]:
    """Map the legacy Buy Now patch checks onto their verification results."""

    return {
        "desktop_mouse": checks["correct_selector"] and checks["click_handler"],
        "mobile_layout": checks["correct_selector"],
        "keyboard_activation": checks["semantic_button"] and checks["click_handler"],
        "focus_visibility": True,
        "console_clean": all(
            checks[key]
            for key in ("correct_selector", "safe_initialization", "null_guard")
        ),
        "repeated_clicks": checks["click_handler"],
        "regression": checks["semantic_button"],
    }
