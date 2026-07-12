from datetime import datetime, timezone
from typing import Any

from services.firebase_service import get_database_reference


def save_simulation_result(
    user_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    scenario_id: str,
    answers: dict[str, Any],
    result: dict[str, Any]
) -> str:
    """Save one completed simulation result in Firebase."""

    if not user_id:
        raise ValueError(
            "A logged-in user is required to save a simulation result."
        )

    simulation_data = {
        "user_id": user_id,
        "career_id": career_id,
        "position_id": position_id,
        "company_id": company_id,
        "scenario_id": scenario_id,
        "answers": answers,
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    results_reference = get_database_reference(
        "simulation_results"
    )

    new_result_reference = results_reference.push(
        simulation_data
    )

    if not new_result_reference.key:
        raise RuntimeError(
            "Firebase did not create a simulation result ID."
        )

    return new_result_reference.key