from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from services.firebase_service import get_database_reference



def _current_utc_time() -> str:
    """Return the current UTC time in a Firebase-safe string format."""
    return datetime.now(timezone.utc).isoformat()


def get_simulation_attempt(
    *,
    user_id: str,
    attempt_id: str,
) -> dict[str, Any] | None:
    """Retrieve one simulation attempt belonging to a user."""

    if not user_id or not attempt_id:
        return None

    attempt = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    ).get()

    if not isinstance(attempt, dict):
        return None

    return attempt


def create_workplace_simulation_attempt(
    *, user_id: str, career_id: str, position_id: str, company_id: str,
) -> str:
    """Create a workplace attempt awaiting one generated scenario."""
    if not user_id:
        raise ValueError("A logged-in user ID is required to create a simulation.")
    attempts = get_database_reference(f"users/{user_id}/simulation_attempts")
    reference = attempts.push()
    attempt_id = reference.key
    if not attempt_id:
        raise RuntimeError("Firebase did not create a simulation attempt ID.")
    record = {
        "simulation_mode": "workplace",
        "career_id": career_id,
        "position_id": position_id,
        "company_id": company_id,
        "status": "generating",
        "created_at": _current_utc_time(),
        "scenario_version": 1,
    }
    reference.set(record)
    return attempt_id


def save_workplace_scenario(
    *,
    user_id: str,
    attempt_id: str,
    public_scenario: dict[str, Any],
    private_context: dict[str, Any],
    generation_attempt_count: int,
) -> None:
    """Persist the validated scenario on its existing canonical attempt."""
    if not user_id or not attempt_id:
        raise ValueError("A user ID and workplace attempt ID are required.")
    if not isinstance(public_scenario, dict) or not isinstance(private_context, dict):
        raise ValueError("Both public and private scenario data are required.")
    reference = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    )
    existing_attempt = reference.get()
    if not isinstance(existing_attempt, dict) or existing_attempt.get("simulation_mode") != "workplace":
        raise RuntimeError("The workplace attempt could not be found.")
    if existing_attempt.get("public_scenario") or existing_attempt.get("private_context"):
        raise RuntimeError("The workplace attempt already has a scenario.")
    generated_at = _current_utc_time()
    reference.update(
        {
            "public_scenario": deepcopy(public_scenario),
            "private_context": deepcopy(private_context),
            "generation": {
                "source": "gemini",
                "generated_at": generated_at,
                "attempt_count": generation_attempt_count,
            },
            "status": "in_progress",
            "updated_at": generated_at,
        }
    )


def mark_workplace_generation_failed(*, user_id: str, attempt_id: str) -> None:
    """Mark a new attempt unusable when bounded scenario generation fails."""
    if not user_id or not attempt_id:
        raise ValueError("A user ID and workplace attempt ID are required.")
    reference = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    )
    existing_attempt = reference.get()
    if not isinstance(existing_attempt, dict) or existing_attempt.get("simulation_mode") != "workplace":
        raise RuntimeError("The workplace attempt could not be found.")
    if existing_attempt.get("public_scenario") or existing_attempt.get("private_context"):
        raise RuntimeError("A generated workplace attempt cannot be marked failed.")
    reference.update({"status": "generation_failed", "updated_at": _current_utc_time()})


def save_simulation_step_response(
    *,
    user_id: str,
    attempt_id: str,
    step: int,
    response: dict[str, Any],
) -> None:
    """
    Save one validated simulation response in Firebase.

    The response is stored under the existing simulation attempt.
    """

    if not user_id:
        raise ValueError(
            "A logged-in user ID is required."
        )

    if not attempt_id:
        raise ValueError(
            "A simulation attempt ID is required."
        )

    if step < 1 or step > 5:
        raise ValueError(
            "Simulation step must be between 1 and 5."
        )

    if not isinstance(response, dict):
        raise ValueError(
            "Simulation response must be a dictionary."
        )

    attempt_reference = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    )

    existing_attempt = attempt_reference.get()

    if not isinstance(existing_attempt, dict):
        raise RuntimeError(
            "The simulation attempt could not be found."
        )

    if existing_attempt.get("status") != "in_progress":
        raise RuntimeError(
            "This simulation attempt is no longer active."
        )

    submitted_at = _current_utc_time()

    stored_response = deepcopy(response)
    stored_response["submitted_at"] = submitted_at

    next_step = min(step + 1, 5)

    attempt_reference.update(
        {
            f"responses/step_{step}": stored_response,
            "current_step": next_step,
            "updated_at": submitted_at,
        }
    )

def save_simulation_evaluation(
    *,
    user_id: str,
    attempt_id: str,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """
    Save Gemini's evaluation and mark the simulation as complete.
    """

    if not user_id:
        raise ValueError(
            "A logged-in user ID is required."
        )

    if not attempt_id:
        raise ValueError(
            "A simulation attempt ID is required."
        )

    if not isinstance(evaluation, dict):
        raise ValueError(
            "Evaluation must be a dictionary."
        )

    attempt_reference = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    )

    existing_attempt = attempt_reference.get()

    if not isinstance(existing_attempt, dict):
        raise RuntimeError(
            "The simulation attempt could not be found."
        )

    public_evaluation = get_user_visible_evaluation(evaluation)
    if not public_evaluation:
        raise ValueError("Evaluation has no user-visible report fields.")

    completed_at = _current_utc_time()

    attempt_reference.update({
        "evaluation": public_evaluation,
        "status": "completed",
        "current_step": 5,
        "completed_at": completed_at,
        "updated_at": completed_at,
    })
    return deepcopy(public_evaluation)

_USER_VISIBLE_EVALUATION_FIELDS = {
    "overall_score",
    "summary",
    "dimensions",
    "strengths",
    "areas_for_improvement",
    "advisor_feedback",
    "recommended_next_steps",
    "recommended_skills",
    "review_message",
    "step_feedback",
    "frontend_readiness",
}


def get_user_visible_evaluation(evaluation: Any) -> dict[str, Any] | None:
    """Return only report fields intended for the simulation owner."""
    if not isinstance(evaluation, dict):
        return None
    if isinstance(evaluation.get("data"), dict):
        evaluation = evaluation["data"]

    public = {
        key: deepcopy(value)
        for key, value in evaluation.items()
        if key in _USER_VISIBLE_EVALUATION_FIELDS
    }
    return public or None


def _attempt_task_title(attempt: dict[str, Any]) -> str | None:
    """Find the canonical public task subject across attempt generations."""
    public_scenario = attempt.get("public_scenario")
    if isinstance(public_scenario, dict):
        task = public_scenario.get("task")
        if isinstance(task, dict):
            title = task.get("subject") or task.get("title")
            if title:
                return str(title).strip()

    return None


def list_user_simulation_attempts(user_id: str) -> list[dict[str, Any]]:
    """Return safe dashboard history for one Firebase user, newest first."""

    if not user_id:
        return []

    attempts = get_database_reference(
        f"users/{user_id}/simulation_attempts"
    ).get()

    if not isinstance(attempts, dict):
        return []

    summaries: list[dict[str, Any]] = []

    for attempt_id, attempt in attempts.items():
        if not isinstance(attempt, dict):
            continue

        status = str(attempt.get("status") or "in_progress")
        if status not in {
            "completed", "in_progress", "generating", "generation_failed"
        }:
            status = "in_progress"

        summaries.append(
            {
                "attempt_id": attempt_id,
                "career_id": attempt.get("career_id"),
                "position_id": attempt.get("position_id"),
                "company_id": attempt.get("company_id"),
                "simulation_mode": attempt.get("simulation_mode"),
                "task_title": _attempt_task_title(attempt),
                "status": status,
                "created_at": attempt.get("created_at"),
                "updated_at": attempt.get("updated_at"),
                "completed_at": attempt.get("completed_at"),
                "evaluation": get_user_visible_evaluation(attempt.get("evaluation")),
            }
        )

    summaries.sort(
        key=lambda item: (
            item.get("completed_at")
            or item.get("updated_at")
            or item.get("created_at")
            or ""
        ),
        reverse=True,
    )
    return summaries


def save_frontend_workplace_progress(
    *, user_id: str, attempt_id: str, step: int, response: dict[str, Any]
) -> None:
    """Persist one validated Frontend desktop task in its owned attempt."""
    save_simulation_step_response(
        user_id=user_id, attempt_id=attempt_id, step=step, response=response
    )


def get_frontend_workplace_progress(*, user_id: str, attempt_id: str) -> dict[str, Any] | None:
    """Return only the owner's public Frontend progress and report."""
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if not attempt or attempt.get("position_id") != "frontend-developer":
        return None
    return {
        "attempt_id": attempt_id,
        "status": attempt.get("status"),
        "current_step": attempt.get("current_step", 1),
        "responses": deepcopy(attempt.get("responses", {})),
        "evaluation": get_user_visible_evaluation(attempt.get("evaluation")),
    }
