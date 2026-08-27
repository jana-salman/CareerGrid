"""Dashboard route and presentation helpers."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, session, url_for

from constants import WORKPLACE_SIMULATION_MODE
from services.career_service import (
    get_career_display_name,
    get_company_display_name,
    get_position_title,
)
from services.simulation_storage import list_user_simulation_attempts


dashboard_bp = Blueprint("dashboard", __name__)

# =========================================================
# DASHBOARD HELPERS
# =========================================================

def _format_dashboard_date(timestamp):
    """Format an ISO attempt timestamp consistently and defensively."""
    if not timestamp:
        return "Unknown date"

    try:
        cleaned = str(timestamp).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"
    except (ValueError, TypeError):
        return str(timestamp)


def _build_dashboard_item(summary):
    """Prepare one simulation attempt for the dashboard."""

    career_id = summary.get("career_id")
    position_id = summary.get("position_id")
    company_id = summary.get("company_id")
    evaluation = summary.get("evaluation")
    score = evaluation.get("overall_score") if isinstance(evaluation, dict) else None
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        score = None
    elif isinstance(score, float) and score.is_integer():
        score = int(score)

    raw_status = summary.get("status")
    status_labels = {
        "completed": "Completed",
        "in_progress": "In Progress",
        "generating": "In Progress",
        "generation_failed": "Generation Failed",
    }
    timestamp = (
        summary.get("completed_at")
        or summary.get("updated_at")
        or summary.get("created_at")
    )
    feedback_preview = ""
    if isinstance(evaluation, dict):
        feedback_preview = (
            evaluation.get("summary")
            or evaluation.get("advisor_feedback")
            or evaluation.get("review_message")
            or ""
        )

    return {
        "attempt_id": summary.get("attempt_id"),
        "task_title": summary.get("task_title") or "Workplace simulation",
        "career_name": get_career_display_name(career_id),
        "position_title": get_position_title(
            career_id,
            position_id,
        ),
        "company_name": get_company_display_name(
            career_id,
            position_id,
            company_id,
        ),
        "date": _format_dashboard_date(timestamp),
        "score": score,
        "status": raw_status,
        "status_label": status_labels.get(raw_status, "In Progress"),
        "feedback_preview": str(feedback_preview).strip(),
        "evaluation": evaluation,
        "can_resume": (
            raw_status == "in_progress"
            and summary.get("simulation_mode") == WORKPLACE_SIMULATION_MODE
        ),
    }


# =========================================================
# DASHBOARD ROUTES
# =========================================================

@dashboard_bp.route("/dashboard")
def dashboard():
    """Show the signed-in user's Firebase simulation history."""

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    summaries = [
        summary
        for summary in list_user_simulation_attempts(user_id)
        if summary.get("simulation_mode") == WORKPLACE_SIMULATION_MODE
    ]

    attempts = [
        _build_dashboard_item(summary)
        for summary in summaries
    ]

    completed_count = sum(
        attempt["status"] == "completed" for attempt in attempts
    )
    scores = [
        attempt["score"] for attempt in attempts
        if attempt["status"] == "completed" and attempt["score"] is not None
    ]
    average_score = round(sum(scores) / len(scores)) if scores else None
    reports = {
        attempt["attempt_id"]: {
            "evaluation": attempt["evaluation"],
            "meta": {
                "task": attempt["task_title"],
                "position": attempt["position_title"],
                "company": attempt["company_name"],
            },
        }
        for attempt in attempts
        if attempt["attempt_id"] and attempt["evaluation"]
    }

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        attempts=attempts,
        simulation_count=len(attempts),
        completed_count=completed_count,
        average_score=average_score,
        reports=reports,
    )
