from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from services.firebase_service import get_database_reference



def _current_utc_time() -> str:
    """Return the current UTC time in a Firebase-safe string format."""
    return datetime.now(timezone.utc).isoformat()


def _split_inbox_task(
    generated_task: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Separate user-visible inbox content from hidden scoring data.

    The user-visible task does not include:
    - the answer key
    - the hidden priority assigned to each email
    """

    public_task = deepcopy(generated_task)

    # Remove the main answer key from the visible task.
    answer_key = public_task.pop("answer_key", {})

    email_priorities = {}

    for email in public_task.get("emails", []):
        email_id = email.get("id")

        # Remove hidden priority before storing the user-visible copy.
        priority = email.pop("priority", None)

        if email_id and priority:
            email_priorities[email_id] = priority

    private_scoring_data = {
        "answer_key": answer_key,
        "email_priorities": email_priorities,
    }

    return public_task, private_scoring_data


def create_backend_simulation_attempt(
    *,
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    generated_inbox_task: dict[str, Any],
) -> str:
    """
    Create a new Backend Developer simulation attempt.

    Returns:
        The unique Firebase simulation attempt ID.
    """

    if not user_id:
        raise ValueError(
            "A logged-in user ID is required to create a simulation."
        )

    public_task, private_scoring_data = _split_inbox_task(
        generated_inbox_task
    )

    attempts_reference = get_database_reference(
        f"users/{user_id}/simulation_attempts"
    )

    # Firebase creates a unique ID for this simulation attempt.
    new_attempt_reference = attempts_reference.push()
    attempt_id = new_attempt_reference.key

    if not attempt_id:
        raise RuntimeError(
            "Firebase did not create a simulation attempt ID."
        )

    created_at = _current_utc_time()

    public_attempt_data = {
        "career_id": career_id,
        "position_id": position_id,
        "company_id": company_id,
        "status": "in_progress",
        "current_step": 1,
        "created_at": created_at,
        "completed_at": None,
        "generated_tasks": {
            "step_1": public_task
        },
        "responses": {},
        "evaluation": None,
        "roadmap": None,
    }

    private_attempt_data = {
        "owner_user_id": user_id,
        "career_id": career_id,
        "position_id": position_id,
        "company_id": company_id,
        "created_at": created_at,
        "task_scoring": {
            "step_1": private_scoring_data
        },
    }

    try:
        # Save information that may later be displayed to the user.
        new_attempt_reference.set(public_attempt_data)

        # Save hidden answers separately.
        get_database_reference(
            f"private_simulation_data/{attempt_id}"
        ).set(private_attempt_data)

    except Exception:
        # Avoid leaving a partially created public attempt.
        try:
            new_attempt_reference.delete()
        except Exception:
            pass

        raise

    return attempt_id


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


def get_backend_inbox_task(
    *,
    user_id: str,
    attempt_id: str,
) -> dict[str, Any] | None:
    """Retrieve the saved public inbox task for an attempt."""

    attempt = get_simulation_attempt(
        user_id=user_id,
        attempt_id=attempt_id,
    )

    if not attempt:
        return None

    generated_tasks = attempt.get("generated_tasks", {})
    inbox_task = generated_tasks.get("step_1")

    if not isinstance(inbox_task, dict):
        return None

    return inbox_task

def create_frontend_simulation_attempt(
    *,
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    generated_inbox_task: dict[str, Any],
) -> str:
    """
    Create a new Frontend Developer simulation attempt.

    The Frontend inbox has the same structure as the Backend inbox,
    so this reuses the shared attempt-creation logic. It returns the
    unique Firebase simulation attempt ID.
    """

    return create_backend_simulation_attempt(
        user_id=user_id,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        generated_inbox_task=generated_inbox_task,
    )

def create_ux_simulation_attempt(
    *,
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    generated_inbox_task: dict[str, Any],
) -> str:
    """
    Create a new UX Designer simulation attempt.

    The UX inbox has the same structure as the Backend and Frontend
    inboxes, so this reuses the shared attempt-creation logic.
    """

    return create_backend_simulation_attempt(
        user_id=user_id,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        generated_inbox_task=generated_inbox_task,
    )

def create_data_analyst_simulation_attempt(
    *,
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    generated_inbox_task: dict[str, Any],
) -> str:
    """
    Create a new Data Analyst simulation attempt.

    The Data Analyst inbox uses the same shared inbox
    storage structure as the existing simulations.
    """

    return create_backend_simulation_attempt(
        user_id=user_id,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        generated_inbox_task=generated_inbox_task,
    )


def create_ui_simulation_attempt(
    *,
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    generated_inbox_task: dict,
) -> str:
    """
    Create a new UI Designer simulation attempt.

    The UI inbox uses the same stored attempt structure
    as the Backend, Frontend, and UX simulations.
    """

    return create_backend_simulation_attempt(
        user_id=user_id,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        generated_inbox_task=generated_inbox_task,
    )

def get_frontend_inbox_task(
    *,
    user_id: str,
    attempt_id: str,
) -> dict[str, Any] | None:
    """Retrieve the saved public inbox task for a frontend attempt."""

    return get_backend_inbox_task(
        user_id=user_id,
        attempt_id=attempt_id,
    )

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

def save_simulation_roadmap(
    *,
    user_id: str,
    attempt_id: str,
    roadmap: dict[str, Any],
) -> None:
    """
    Save the personalized roadmap inside the completed
    Firebase simulation attempt.
    """

    if not user_id:
        raise ValueError(
            "A logged-in user ID is required."
        )

    if not attempt_id:
        raise ValueError(
            "A simulation attempt ID is required."
        )

    if not isinstance(roadmap, dict):
        raise ValueError(
            "Roadmap must be a dictionary."
        )

    attempt_reference = get_database_reference(
        f"users/{user_id}/simulation_attempts/{attempt_id}"
    )

    existing_attempt = attempt_reference.get()

    if not isinstance(existing_attempt, dict):
        raise RuntimeError(
            "The simulation attempt could not be found."
        )

    if not isinstance(
        existing_attempt.get("evaluation"),
        dict,
    ):
        raise RuntimeError(
            "The simulation must be evaluated before "
            "a roadmap can be saved."
        )

    updated_at = _current_utc_time()

    attempt_reference.update({
        "roadmap": deepcopy(roadmap),
        "updated_at": updated_at,
    })
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

    generated_tasks = attempt.get("generated_tasks")
    if isinstance(generated_tasks, dict):
        first_task = generated_tasks.get("step_1")
        if isinstance(first_task, dict):
            title = first_task.get("subject") or first_task.get("title")
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


def list_completed_simulation_attempts(
    user_id: str,
) -> list[dict[str, Any]]:
    """Backward-compatible completed-attempt summaries."""
    return [
        {
            **attempt,
            "overall_score": (
                attempt.get("evaluation", {}).get("overall_score", 0)
                if isinstance(attempt.get("evaluation"), dict)
                else 0
            ),
        }
        for attempt in list_user_simulation_attempts(user_id)
        if attempt.get("status") == "completed"
    ]
