"""Dashboard route and presentation helpers."""

from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, session, url_for

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


def _build_dashboard_item(summary, *, include_evaluation=True):
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

    item = {
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
        "has_evaluation": bool(evaluation),
        "can_resume": (
            raw_status == "in_progress"
            and summary.get("simulation_mode") == WORKPLACE_SIMULATION_MODE
        ),
    }

    if include_evaluation:
        item["evaluation"] = evaluation

    return item


def _dashboard_payload(user_id, *, include_evaluations=True):
    """Build the display-safe dashboard response for one signed-in user."""

    summaries = [summary for summary in list_user_simulation_attempts(user_id)
                 if summary.get("simulation_mode") == WORKPLACE_SIMULATION_MODE]
    attempts = [
        _build_dashboard_item(
            summary,
            include_evaluation=include_evaluations,
        )
        for summary in summaries
    ]
    scores = [attempt["score"] for attempt in attempts
              if attempt["status"] == "completed" and attempt["score"] is not None]
    return {
        "user_id": user_id,
        "user_name": session.get("user_name"),
        "attempts": attempts,
        "simulation_count": len(attempts),
        "completed_count": sum(attempt["status"] == "completed" for attempt in attempts),
        "average_score": round(sum(scores) / len(scores)) if scores else None,
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

    payload = _dashboard_payload(user_id)
    attempts = payload["attempts"]
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
        user_name=payload["user_name"],
        attempts=attempts,
        simulation_count=payload["simulation_count"],
        completed_count=payload["completed_count"],
        average_score=payload["average_score"],
        reports=reports,
    )


@dashboard_bp.get("/api/dashboard")
def dashboard_api():
    """Return the signed-in user's display-safe dashboard data."""

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401
    return jsonify(
        _dashboard_payload(
            user_id,
            include_evaluations=False,
        )
    )
