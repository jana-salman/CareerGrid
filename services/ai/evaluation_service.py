"""Evaluate workplace evidence while keeping private rubrics server-side."""

import json
from typing import Any

from google.genai import types

from ai_prompt.prompts.workplace_evaluation_v4 import EVALUATION_SCHEMA, build_workplace_evaluation_prompt
from config import get_gemini_model
from services.ai.gemini_service import get_gemini_client
from services.ai.gemini_utils import clean_json_response
from services.ai.roadmap import (
    DIMENSION_SKILLS,
    match_resources,
    normalize_review_items,
    normalize_roadmap,
    readable_text,
)

__all__ = ["normalize_review_items", "normalize_roadmap"]  # re-exported for routes


class SimulationEvaluationError(Exception):
    """Raised when Gemini cannot produce a valid evaluation."""


VERIFICATION_NOTE = (
    "The simulated workspace cannot execute tests or run code. Testing you "
    "described is treated as a written claim; automated results, where shown, "
    "come from CareerGrid's static checks of your submitted files."
)

LEGACY_CHECK_CATEGORIES = {
    "correct_selector": "correctness",
    "safe_initialization": "robustness",
    "null_guard": "robustness",
    "click_handler": "correctness",
    "semantic_button": "accessibility",
}

DIMENSION_LABELS = {
    "triage_and_prioritization": "Triage and prioritization",
    "investigation": "Investigation",
    "root_cause_reasoning": "Root-cause reasoning",
    "implementation_quality": "Implementation quality",
    "testing_and_verification": "Testing and verification",
    "accessibility": "Accessibility",
    "regression_awareness": "Regression awareness",
    "git_and_pr_workflow": "Git and PR workflow",
    "communication": "Communication",
    "scope_and_independence": "Scope and independence",
}

NEXT_STEPS = {
    "triage_and_prioritization": [
        "Practise ranking a mixed inbox by user impact and urgency, and write one sentence justifying each ranking.",
    ],
    "investigation": [
        "Reproduce issues at several viewport widths and note the exact evidence (console, elements, network) you used.",
    ],
    "root_cause_reasoning": [
        "Write a short 'symptom -> evidence -> cause' chain before changing code.",
    ],
    "implementation_quality": [
        "Re-read each requirement in the task, then compare it with your final file contents line by line.",
        "Practise defensive DOM code: confirm elements exist before using them and initialise after the document is ready.",
    ],
    "testing_and_verification": [
        "Turn each requirement into a concrete check you can repeat (input, action, expected result).",
        "Separate what you actually ran from what you reasoned about when reporting verification.",
    ],
    "accessibility": [
        "Check keyboard-only use (Tab, Enter, Space) and visible focus for every interactive element you change.",
    ],
    "regression_awareness": [
        "List the behaviours your change could affect and re-check them after the fix.",
    ],
    "git_and_pr_workflow": [
        "Practise the branch -> commit -> push -> pull request flow so changes can be reviewed before reaching main.",
        "Write commit messages that state what changed and why in under 72 characters.",
    ],
    "communication": [
        "End each task with a three-part update: what you found, what you changed, how you verified it.",
    ],
    "scope_and_independence": [
        "Keep the change limited to the files the requirement needs and explain any extra file you touch.",
    ],
}


def _score(*conditions: bool) -> int:
    return round(10 * sum(bool(item) for item in conditions) / max(len(conditions), 1))


def _fraction_score(results: list[bool]) -> int | None:
    if not results:
        return None
    return round(10 * sum(bool(item) for item in results) / len(results))


def _git_workflow(delivery: dict[str, Any]) -> tuple[int, str]:
    """Score Git delivery separately from technical quality."""

    mode = delivery.get("delivery_mode") or "pull_request"
    evidence = delivery.get("delivery_evidence") or {}
    if mode == "main":
        score = _score(
            bool(delivery.get("commit_message")),
            bool(evidence.get("pushed")),
            len(delivery.get("final_team_message", "")) >= 40,
            bool(delivery.get("testing_checklist")),
        )
        return score, (
            "You committed and pushed directly to main, which is an accepted way to deliver here. "
            "On most teams a short-lived feature branch and a pull request let a colleague review "
            "the change before it reaches main, so practise that flow next time. Your technical "
            "work was assessed independently of this choice."
        )
    score = _score(
        bool(delivery.get("commit_message")),
        bool(delivery.get("pr_title")),
        len(delivery.get("pr_description", "")) >= 40,
        bool(delivery.get("testing_checklist")),
    )
    return score, (
        "You delivered through a pull request, which gives reviewers a clear diff and description."
    )


def _roadmap_evidence(key: str, responses: dict[str, Any], failed_checks: list[str]) -> str:
    implementation = responses.get("step_3", {})
    verification = responses.get("step_4", {})
    delivery = responses.get("step_5", {})
    files = ", ".join(sorted(implementation.get("changed_files", {}))) or "no files"
    if key == "implementation_quality":
        if failed_checks:
            return f"In your submitted changes to {files}, {len(failed_checks)} automated check(s) did not pass."
        return f"Your submitted changes touched {files}."
    if key == "testing_and_verification":
        results = verification.get("verified_results", {})
        claimed = ", ".join(verification.get("commands_run", [])) or "none listed"
        passed = sum(bool(value) for value in results.values())
        return (
            f"You reported running: {claimed} (self-reported). CareerGrid's automated "
            f"checks passed {passed}/{len(results)}."
        )
    if key == "git_and_pr_workflow":
        mode = delivery.get("delivery_mode") or "pull_request"
        route = "a pull request" if mode == "pull_request" else "a direct push to main"
        return f"You delivered via {route} with the commit message \"{delivery.get('commit_message', '')}\"."
    if key == "communication":
        return f"Your final team update was {len(delivery.get('final_team_message', ''))} characters long."
    if key == "investigation":
        viewports = ", ".join(responses.get("step_2", {}).get("viewports_tested", [])) or "none"
        return f"You recorded these viewports: {viewports}."
    if key == "root_cause_reasoning":
        return f"Your stated root cause: \"{responses.get('step_2', {}).get('selected_root_cause', '')}\"."
    return f"{DIMENSION_LABELS[key]} scored lower than your other areas in this attempt."


def build_frontend_roadmap(
    dimensions: dict[str, int],
    responses: dict[str, Any],
    failed_checks: list[str],
) -> list[dict[str, Any]]:
    """Turn the weakest dimensions into evidence-linked next learning steps."""

    ranked = sorted(dimensions.items(), key=lambda item: item[1])
    gaps = [item for item in ranked if item[1] < 7][:3] or ranked[:1]
    return [
        {
            "skill": DIMENSION_LABELS[key],
            "evidence": _roadmap_evidence(key, responses, failed_checks),
            "gap": (
                f"{DIMENSION_LABELS[key]} scored {value}/10."
                if value < 7
                else f"{DIMENSION_LABELS[key]} was your lowest area ({value}/10); treat it as a stretch goal."
            ),
            "next_steps": list(NEXT_STEPS[key]),
            "resources": match_resources(DIMENSION_SKILLS[key]),
        }
        for key, value in gaps
    ]


def evaluate_frontend_workplace_progress(
    responses: dict[str, Any],
    private_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, offline-capable review from validated evidence."""

    private_context = private_context or {}
    investigation = responses.get("step_2", {})
    implementation = responses.get("step_3", {})
    verification = responses.get("step_4", {})
    delivery = responses.get("step_5", {})
    checks = implementation.get("patch_checks", {}) or {}
    categories = implementation.get("check_categories") or {
        key: LEGACY_CHECK_CATEGORIES.get(key, "correctness") for key in checks
    }
    test_results = verification.get("verified_results", {})

    def by_category(*names: str) -> list[bool]:
        return [bool(checks[key]) for key in checks if categories.get(key) in names]

    keywords = [
        str(item).lower()
        for item in private_context.get("root_cause_keywords", []) or []
        if str(item).strip()
    ]
    reasoning_text = (
        f"{investigation.get('selected_root_cause', '')} "
        f"{investigation.get('investigation_summary', '')}"
    ).lower()
    if keywords:
        root_cause = _fraction_score([keyword in reasoning_text for keyword in keywords])
    else:
        root_cause = _score(
            "selector" in investigation.get("selected_root_cause", "").lower(),
            "buy" in investigation.get("investigation_summary", "").lower(),
        )

    if "keyboard_activation" in test_results:
        # Legacy Buy Now attempts keep their original scoring.
        accessibility = _score(
            test_results.get("keyboard_activation"),
            test_results.get("focus_visibility"),
            checks.get("semantic_button"),
        )
        regression = _score(
            test_results.get("regression"),
            test_results.get("repeated_clicks"),
            test_results.get("console_clean"),
        )
    else:
        accessibility = _fraction_score(by_category("accessibility"))
        if accessibility is None:
            accessibility = _score(bool(verification.get("accessibility_checks")))
        regression = _fraction_score(by_category("regression", "robustness"))
        if regression is None:
            regression = _score(bool(verification.get("tests_performed")))

    git_score, git_feedback = _git_workflow(delivery)
    dimensions = {
        "triage_and_prioritization": _score(
            bool(responses.get("step_1", {}).get("written_response")),
            str(responses.get("step_1", {}).get("selected_priority", "")).lower() == "critical",
        ),
        "investigation": _score(
            len(investigation.get("viewports_tested", [])) >= 2,
            bool(investigation.get("evidence_opened")),
            bool(investigation.get("investigation_summary")),
        ),
        "root_cause_reasoning": root_cause,
        "implementation_quality": _fraction_score([bool(value) for value in checks.values()]) or 0,
        "testing_and_verification": _score(
            bool(verification.get("commands_run")),
            len(verification.get("viewport_checks", [])) >= 2,
            bool(verification.get("accessibility_checks")),
            all(test_results.values()) if test_results else False,
        ),
        "accessibility": accessibility,
        "regression_awareness": regression,
        "git_and_pr_workflow": git_score,
        "communication": _score(
            len(delivery.get("final_team_message", "")) >= 40,
            bool(delivery.get("release_recommendation")),
            len(responses.get("step_1", {}).get("written_response", "")) >= 30,
        ),
        "scope_and_independence": _score(
            set(delivery.get("reviewed_files", []))
            == set(delivery.get("source_step_3_files", [])),
            len(implementation.get("changed_files", {})) <= 3,
            bool(investigation.get("proposed_next_action")),
        ),
    }
    failed_checks = [key for key, value in checks.items() if not value]
    normalized = {
        key: {
            "score": value,
            "max_score": 10,
            "feedback": (
                git_feedback
                if key == "git_and_pr_workflow"
                else f"{DIMENSION_LABELS[key]} evidence earned {value}/10."
            ),
        }
        for key, value in dimensions.items()
    }
    overall = round(sum(dimensions.values()))
    strengths = [
        DIMENSION_LABELS[key] for key, value in dimensions.items() if value >= 8
    ] or ["Completed the full workplace workflow"]
    improvements = [
        DIMENSION_LABELS[key] for key, value in dimensions.items() if value < 7
    ] or ["Keep documenting edge-case verification"]
    readiness = (
        "Ready for guided junior frontend work"
        if overall >= 75
        else "Developing junior frontend readiness"
    )
    roadmap = build_frontend_roadmap(dimensions, responses, failed_checks)
    return {
        "overall_score": overall,
        "summary": f"You completed the frontend workplace workflow with a score of {overall}/100.",
        "dimensions": normalized,
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "recommended_next_steps": [step for item in roadmap for step in item["next_steps"]][:4],
        "personalized_roadmap": roadmap,
        "git_workflow_feedback": git_feedback,
        "verification_note": VERIFICATION_NOTE,
        "advisor_feedback": (
            "Use the evidence trail - from report to diagnosis, patch, and checks - "
            "to make each decision auditable."
        ),
        "review_message": (
            "Your frontend workplace review is ready. Open the report for the "
            "evidence-based score, your roadmap, and next steps."
        ),
        "frontend_readiness": readiness,
    }


def build_submission_overview(user_evidence: dict[str, Any]) -> dict[str, Any]:
    """Describe the frozen submission from recorded evidence, not model output."""

    repository = user_evidence.get("repository") or {}
    pull_request = user_evidence.get("pull_request") or {}
    comparison = user_evidence.get("comparison") or {}
    return {
        "mode": user_evidence.get("submission_mode") or ("pull_request" if pull_request else "unknown"),
        "branch": str(repository.get("branch") or ""),
        "commit_id": str(repository.get("commit_id") or ""),
        "pull_request_url": str(pull_request.get("url") or ""),
        "changed_files": [
            str(item.get("path"))
            for item in user_evidence.get("changed_files", [])
            if isinstance(item, dict) and item.get("path")
        ][:30],
        "comparison_basis": str(comparison.get("basis") or ""),
        "verification_note": VERIFICATION_NOTE,
    }


# Skill-specific next steps for Gemini-evaluated dimensions, used only when the
# evaluator's roadmap is unusable. Each card keeps its own steps.
BACKEND_NEXT_STEPS = {
    "technical_accuracy": [
        "Re-read each requirement and check the matching code path handles it, including the error responses.",
        "List the edge cases the task names (empty, invalid, duplicate, missing) and confirm each one in code.",
    ],
    "problem_solving": [
        "Before editing, trace one failing example from the evidence through each module it touches.",
        "Write the cause as 'symptom -> evidence -> cause' and check it against the logs or ticket.",
    ],
    "verification_testing": [
        "Add one regression test per requirement, plus one for the behaviour that must stay unchanged.",
        "In your handover, separate tests you wrote from checks you only reasoned through.",
    ],
    "git_workflow": [
        "Practise branch -> commit -> push -> pull request so a colleague can review before main changes.",
        "Write commit messages that say what changed and why in one short line.",
    ],
    "communication": [
        "End each task with a three-part update: what you found, what you changed, how you verified it.",
        "Name the files you changed and any remaining risks in your handover.",
    ],
    "independence": [
        "Keep the change to the files the requirements need, and explain any extra file you touch.",
        "Use the README and evidence files to answer questions before asking for help.",
    ],
}


def _fallback_roadmap(evaluation: dict[str, Any], overview: dict[str, Any]) -> list[dict[str, Any]]:
    """Roadmap from the weakest scored dimensions, each with its own steps."""

    dimensions = evaluation.get("dimensions") or {}
    scored = []
    for key, item in dimensions.items():
        if isinstance(item, dict) and isinstance(item.get("score"), (int, float)) and key in BACKEND_NEXT_STEPS:
            maximum = item.get("max_score") or 10
            scored.append((item["score"] / maximum if maximum else 0, key, item))
    files = ", ".join(overview["changed_files"]) or "your submission"
    return normalize_roadmap([
        {
            "skill": key.replace("_", " ").title(),
            "evidence": f"Based on your submitted changes to {files}: {readable_text(item.get('feedback'), 400)}".strip(),
            "gap": f"Scored {item.get('score')}/{item.get('max_score') or 10}.",
            "next_steps": list(BACKEND_NEXT_STEPS[key]),
            "resources": [entry["id"] for entry in match_resources(DIMENSION_SKILLS[key])],
        }
        for _, key, item in sorted(scored)[:3]
    ])


def _normalize_workplace_evaluation(
    evaluation: dict[str, Any],
    user_evidence: dict[str, Any],
) -> dict[str, Any]:
    try:
        evaluation["overall_score"] = max(0, min(100, round(float(evaluation.get("overall_score", 0)))))
    except (TypeError, ValueError) as error:
        raise SimulationEvaluationError("Gemini returned an invalid overall score.") from error
    overview = build_submission_overview(user_evidence)
    evaluation["submission_overview"] = overview
    roadmap = normalize_roadmap(
        evaluation.get("personalized_roadmap"),
        extra_sources=(evaluation.get("recommended_next_steps"),),
    )
    evaluation["personalized_roadmap"] = roadmap or _fallback_roadmap(evaluation, overview)
    for key in ("strengths", "areas_for_improvement", "recommended_next_steps"):
        if key in evaluation:
            evaluation[key] = normalize_review_items(evaluation[key])
    if evaluation.get("git_workflow_feedback") is not None:
        evaluation["git_workflow_feedback"] = str(evaluation["git_workflow_feedback"]).strip()[:1200]
    evaluation["verification_note"] = VERIFICATION_NOTE
    return evaluation


def evaluate_workplace_submission(evidence: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a submitted workplace task from recorded simulation evidence."""
    model = get_gemini_model()
    prompt = build_workplace_evaluation_prompt(evidence)
    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=EVALUATION_SCHEMA,
                    temperature=0.35,
                ),
            )
        evaluation = json.loads(clean_json_response(response.text or ""))
    except Exception as error:
        raise SimulationEvaluationError(
            "Gemini could not evaluate the submitted work."
        ) from error
    if not isinstance(evaluation, dict) or not isinstance(evaluation.get("dimensions"), dict):
        raise SimulationEvaluationError("Gemini returned an invalid workplace evaluation.")
    user_evidence = evidence.get("actual_user_evidence", evidence)
    return _normalize_workplace_evaluation(
        evaluation, user_evidence if isinstance(user_evidence, dict) else {}
    )
