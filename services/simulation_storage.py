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
) -> None:
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

    completed_at = _current_utc_time()

    attempt_reference.update({
        "evaluation": deepcopy(evaluation),
        "status": "completed",
        "current_step": 5,
        "completed_at": completed_at,
        "updated_at": completed_at,
    })

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