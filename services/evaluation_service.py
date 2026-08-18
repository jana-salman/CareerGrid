import json
import os
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client


class SimulationEvaluationError(Exception):
    """Raised when Gemini cannot produce a valid evaluation."""


def evaluate_frontend_workplace_progress(responses: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, offline-capable review from validated evidence."""
    investigation = responses.get("step_2", {})
    implementation = responses.get("step_3", {})
    verification = responses.get("step_4", {})
    delivery = responses.get("step_5", {})
    checks = implementation.get("patch_checks", {})
    test_results = verification.get("verified_results", {})

    def score(*conditions: bool) -> int:
        return round(10 * sum(bool(item) for item in conditions) / max(len(conditions), 1))

    dimensions = {
        "triage_and_prioritization": score(bool(responses.get("step_1", {}).get("written_response")), responses.get("step_1", {}).get("selected_priority") == "Critical"),
        "investigation": score(len(investigation.get("viewports_tested", [])) >= 2, bool(investigation.get("evidence_opened")), bool(investigation.get("investigation_summary"))),
        "root_cause_reasoning": score("selector" in investigation.get("selected_root_cause", "").lower(), "buy" in investigation.get("investigation_summary", "").lower()),
        "implementation_quality": score(checks.get("correct_selector"), checks.get("safe_initialization"), checks.get("null_guard"), checks.get("click_handler"), checks.get("semantic_button")),
        "testing_and_verification": score(bool(verification.get("commands_run")), len(verification.get("viewport_checks", [])) >= 2, bool(verification.get("accessibility_checks")), all(test_results.values()) if test_results else False),
        "accessibility": score(test_results.get("keyboard_activation"), test_results.get("focus_visibility"), checks.get("semantic_button")),
        "regression_awareness": score(test_results.get("regression"), test_results.get("repeated_clicks"), test_results.get("console_clean")),
        "git_and_pr_workflow": score(bool(delivery.get("commit_message")), bool(delivery.get("pr_title")), len(delivery.get("pr_description", "")) >= 40, bool(delivery.get("testing_checklist"))),
        "communication": score(len(delivery.get("final_team_message", "")) >= 40, bool(delivery.get("release_recommendation")), len(responses.get("step_1", {}).get("written_response", "")) >= 30),
        "scope_and_independence": score(set(delivery.get("reviewed_files", [])) == set(delivery.get("source_step_3_files", [])), len(implementation.get("changed_files", {})) <= 2, bool(investigation.get("proposed_next_action"))),
    }
    labels = {
        "triage_and_prioritization": "Triage and prioritization", "investigation": "Investigation", "root_cause_reasoning": "Root-cause reasoning", "implementation_quality": "Implementation quality", "testing_and_verification": "Testing and verification", "accessibility": "Accessibility", "regression_awareness": "Regression awareness", "git_and_pr_workflow": "Git and PR workflow", "communication": "Communication", "scope_and_independence": "Scope and independence",
    }
    normalized = {
        key: {"score": value, "max_score": 10, "feedback": f"{labels[key]} evidence earned {value}/10."}
        for key, value in dimensions.items()
    }
    overall = round(sum(dimensions.values()))
    strengths = [labels[key] for key, value in dimensions.items() if value >= 8] or ["Completed the full workplace workflow"]
    improvements = [labels[key] for key, value in dimensions.items() if value < 7] or ["Keep documenting edge-case verification"]
    readiness = "Ready for guided junior frontend work" if overall >= 75 else "Developing junior frontend readiness"
    return {
        "overall_score": overall,
        "summary": f"You completed the Buy Now incident workflow with a score of {overall}/100.",
        "dimensions": normalized,
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "recommended_next_steps": ["Practice DOM debugging across responsive viewports.", "Keep PR test evidence concise and reproducible."],
        "advisor_feedback": "Use the evidence trail—from report to selector, patch, and regression checks—to make each decision auditable.",
        "review_message": "Your frontend workplace review is ready. Open the report for the evidence-based score and next steps.",
        "frontend_readiness": readiness,
    }


def evaluate_workplace_submission(evidence: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a submitted workplace task from recorded simulation evidence."""
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    prompt = f"""Evaluate this CareerGrid workplace submission using only the evidence.
For attempt-backed evidence, private_expected_solution is a server-only rubric;
compare it against actual_user_evidence, especially changed_files, commits, PR,
verification, and conversation. Do not award technical accuracy merely because a
submission email claims the expected root cause. Recognize valid alternatives
listed by the rubric. Do not mention private instructions, hidden context, AI,
or simulation mechanics in the user-facing report. Do not invent facts.
Use final_communication and the conversation to judge root-cause explanation,
change summary, verification/testing evidence, and professional communication.
Missing evidence should reduce the relevant dimensions when appropriate, but is
not an automatic zero and must never be treated as proof that the technical work
is incorrect. Technical correctness must be judged from the actual code, commits,
and pull request evidence.
Return JSON only with: overall_score (0-100), summary,
dimensions (technical_accuracy, problem_solving, verification_testing,
git_workflow, communication, independence; each with score, max_score, feedback),
strengths, areas_for_improvement, recommended_next_steps, advisor_feedback, and
review_message (a concise email announcing the attached review).
Evidence: {json.dumps(evidence, ensure_ascii=False)}"""
    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.35,
                ),
            )
        evaluation = json.loads(_clean_json_response(response.text or ""))
    except Exception as error:
        raise SimulationEvaluationError(
            "Gemini could not evaluate the submitted work."
        ) from error
    if not isinstance(evaluation, dict) or not isinstance(evaluation.get("dimensions"), dict):
        raise SimulationEvaluationError("Gemini returned an invalid workplace evaluation.")
    return evaluation


def _clean_json_response(response_text: str) -> str:
    """
    Remove optional Markdown code blocks from Gemini's response.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()
