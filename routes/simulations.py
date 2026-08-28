"""Workplace simulation pages, reports, and JSON API routes."""

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from constants import (
    FRONTEND_DEVELOPER_POSITION_ID,
    WORKPLACE_FINAL_STEP,
    WORKPLACE_SIMULATION_MODE,
)
from services.simulation.career_service import (
    POSITIONS_DATA,
    get_company_display_name,
    is_position_available,
)
from services.ai.advisor_service import AdvisorReplyError, generate_advisor_reply
from services.simulation.backend_demo_scenario_service import (
    BACKEND_DEMO_JOB_SOURCE,
    get_backend_demo_workplace_scenario,
    is_backend_demo,
)
from services.ai.evaluation_service import (
    SimulationEvaluationError,
    evaluate_frontend_workplace_progress,
    evaluate_workplace_submission,
    normalize_review_items,
)
from services.simulation.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)
from services.simulation.frontend_workplace_scenario_service import generate_frontend_workplace_scenario
from services.ai.scenario_generation_service import ScenarioGenerationError, generate_workplace_scenario
from services.simulation.simulation_storage import (
    create_workplace_simulation_attempt,
    get_frontend_workplace_progress,
    get_simulation_attempt,
    get_user_visible_evaluation,
    mark_workplace_generation_failed,
    save_frontend_workplace_progress,
    save_simulation_evaluation,
    save_workplace_scenario,
)
from routes.frontend import serve_react_app

simulations_bp = Blueprint("simulations", __name__)

@simulations_bp.route("/workspace/<career_id>/<position_id>/<company_id>")
def simulation_workspace(career_id, position_id, company_id):
    """
    Display the persistent desktop workspace for a simulation.
    """

    position_data = POSITIONS_DATA.get(career_id, {}).get(position_id, {})

    # Invalid career/position.
    if not position_data or not is_position_available(career_id, position_id):
        return redirect(url_for("careers.positions", career_id=career_id))

    return serve_react_app()


def _validate_simulation_company(
    career_id: str,
    position_id: str,
    company_id: str,
    job_source: str,
    position: dict,
) -> str | None:
    """
    Validate the company selection for a workplace simulation.

    Returns None if valid, or a redirect URL string if invalid.
    """

    if job_source == BACKEND_DEMO_JOB_SOURCE:
        if not is_backend_demo(career_id, position_id, company_id):
            return url_for(
                "careers.companies",
                career_id=career_id,
                position_id=position_id,
            )
    elif job_source == "adzuna":
        # Live Adzuna jobs use the company name.
        if (
            not company_id
            or len(company_id) > current_app.config["MAX_ADZUNA_COMPANY_NAME_LENGTH"]
        ):
            return url_for(
                "careers.companies",
                career_id=career_id,
                position_id=position_id,
            )
    else:
        # Demo companies must match the IDs in POSITIONS_DATA.
        valid_companies = {
            company.get("id")
            for company in position.get("companies", [])
        }

        if company_id not in valid_companies:
            return url_for(
                "careers.companies",
                career_id=career_id,
                position_id=position_id,
            )

    return None


def _generate_simulation_scenario(
    *,
    career_id: str,
    position_id: str,
    company_id: str,
    attempt_id: str,
    position: dict,
    is_backend_demo_request: bool,
) -> tuple[dict, int, str]:
    """
    Generate and return the workplace scenario for the given attempt.

    Returns (scenario, generation_attempt_count, generation_source).
    Raises ScenarioGenerationError on failure.
    """

    if is_backend_demo_request:
        scenario = get_backend_demo_workplace_scenario(
            attempt_id=attempt_id,
        )
        generation_attempt_count = 1
        generation_source = "predefined_demo"
    elif position_id == FRONTEND_DEVELOPER_POSITION_ID:
        company_name = next(
            (
                company.get("name")
                for company in position.get("companies", [])
                if company.get("id") == company_id
            ),
            company_id,
        )
        scenario, generation_attempt_count = generate_frontend_workplace_scenario(
            company_name=company_name,
            attempt_id=attempt_id,
        )
        generation_source = "gemini"
    else:
        scenario, generation_attempt_count = generate_workplace_scenario(
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            attempt_id=attempt_id,
        )
        generation_source = "gemini"

    return scenario, generation_attempt_count, generation_source


def _handle_generation_failure(
    *,
    user_id: str,
    attempt_id: str | None,
    career_id: str,
    position_id: str,
) -> str:
    """
    Mark the attempt as failed and return the appropriate redirect URL.
    """

    if attempt_id:
        try:
            mark_workplace_generation_failed(
                user_id=user_id,
                attempt_id=attempt_id,
            )
        except Exception:
            current_app.logger.exception("Could not mark workplace generation as failed")
        return url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id)

    return url_for(
        "careers.companies",
        career_id=career_id,
        position_id=position_id,
    )


@simulations_bp.post("/simulation/workplace/start")
def start_workplace_simulation():
    career_id = request.form.get("career_id", "").strip()
    position_id = request.form.get("position_id", "").strip()
    company_id = request.form.get("company_id", "").strip()
    job_source = request.form.get("job_source", "demo").strip().lower()
    is_backend_demo_request = job_source == BACKEND_DEMO_JOB_SOURCE and is_backend_demo(
        career_id, position_id, company_id
    )

    position = POSITIONS_DATA.get(career_id, {}).get(position_id)

    if not position:
        return redirect(url_for("careers.career"))

    if not is_position_available(career_id, position_id):
        return redirect(url_for("careers.positions", career_id=career_id))

    invalid_company_redirect = _validate_simulation_company(
        career_id, position_id, company_id, job_source, position
    )
    if invalid_company_redirect:
        return redirect(invalid_company_redirect)

    attempt_id = None
    workplace_stage = "attempt_creation"
    try:
        attempt_id = create_workplace_simulation_attempt(
            user_id=session.get("user_id"),
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
        )
        current_app.logger.info(
            "Created workplace simulation attempt %s (%s/%s/%s)",
            attempt_id,
            career_id,
            position_id,
            company_id,
        )
        workplace_stage = (
            "predefined_demo_scenario"
            if is_backend_demo_request
            else "frontend_scenario_generation"
            if position_id == FRONTEND_DEVELOPER_POSITION_ID
            else "scenario_generation"
        )
        scenario, generation_attempt_count, generation_source = _generate_simulation_scenario(
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            attempt_id=attempt_id,
            position=position,
            is_backend_demo_request=is_backend_demo_request,
        )
        workplace_stage = "firebase_scenario_storage"
        save_workplace_scenario(
            user_id=session.get("user_id"),
            attempt_id=attempt_id,
            public_scenario=scenario["public_scenario"],
            private_context=scenario["private_context"],
            generation_attempt_count=generation_attempt_count,
            generation_source=generation_source,
        )
        current_app.logger.info(
            "Scenario generation completed for workplace attempt %s",
            attempt_id,
        )
    except ScenarioGenerationError:
        current_app.logger.warning(
            "Scenario generation failed for workplace attempt %s",
            attempt_id,
        )
    except Exception as error:
        current_app.logger.exception(
            "Workplace attempt failed: type=%s attempt_id=%s career_id=%s "
            "position_id=%s stage=%s",
            type(error).__name__,
            attempt_id,
            career_id,
            position_id,
            workplace_stage,
        )
    else:
        return redirect(url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id))

    return redirect(
        _handle_generation_failure(
            user_id=session.get("user_id"),
            attempt_id=attempt_id,
            career_id=career_id,
            position_id=position_id,
        )
    )


@simulations_bp.get("/workspace/attempt/<attempt_id>")
def workplace_attempt_workspace(attempt_id):
    return serve_react_app()


@simulations_bp.get("/simulation/attempts/<attempt_id>/report")
def workplace_task_review(attempt_id):
    """Serve the React workplace report route."""

    return serve_react_app()


@simulations_bp.get("/api/simulation/attempts/<attempt_id>/report")
def workplace_report_api(attempt_id):
    """Return the final, user-visible report for its signed-in owner only."""

    attempt = get_simulation_attempt(
        user_id=session.get("user_id"),
        attempt_id=attempt_id,
    )
    if (
        not attempt
        or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
    ):
        return jsonify({"error": "Simulation attempt not found."}), 404

    evaluation = get_user_visible_evaluation(attempt.get("evaluation"))
    if not evaluation:
        return jsonify({"error": "Simulation report not found."}), 404

    career_id = attempt.get("career_id", "")
    position_id = attempt.get("position_id", "")
    company_id = attempt.get("company_id", "")
    position = POSITIONS_DATA.get(career_id, {}).get(position_id, {})
    valid_demo_company_ids = {
        company.get("id")
        for company in position.get("companies", [])
        if company.get("id")
    }
    if is_backend_demo(career_id, position_id, company_id):
        job_source = BACKEND_DEMO_JOB_SOURCE
    else:
        job_source = "demo" if company_id in valid_demo_company_ids else "adzuna"
    public_scenario = attempt.get("public_scenario", {})
    task = public_scenario.get("task", {}) if isinstance(public_scenario, dict) else {}
    overall_score = evaluation.get("overall_score", 0)
    try:
        interview_unlocked = float(overall_score) >= current_app.config["INTERVIEW_UNLOCK_SCORE"]
    except (TypeError, ValueError):
        interview_unlocked = False

    return jsonify(
        {
            "attempt_id": attempt_id,
            "evaluation": evaluation,
            "task_title": task.get("subject") or task.get("title") or "Workplace Task Review",
            "career_id": career_id,
            "position_id": position_id,
            "company_id": company_id,
            "job_source": job_source,
            "position_title": position.get("title", position_id.replace("-", " ").title()),
            "company_name": get_company_display_name(career_id, position_id, company_id),
            "strengths": normalize_review_items(evaluation.get("strengths")),
            "areas_for_improvement": normalize_review_items(evaluation.get("areas_for_improvement")),
            "recommended_next_steps": normalize_review_items(
                evaluation.get("recommended_next_steps") or evaluation.get("recommended_skills")
            ),
            "interview_unlocked": interview_unlocked,
        }
    )


@simulations_bp.get("/api/simulation/attempts/<attempt_id>")
def get_public_workplace_attempt(attempt_id):
    """Return only browser-safe scenario data for the signed-in user."""
    attempt = get_simulation_attempt(
        user_id=session.get("user_id"),
        attempt_id=attempt_id,
    )
    if not attempt or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE:
        return jsonify({"error": "Simulation attempt not found."}), 404
    return jsonify(
        {
            "attempt_id": attempt_id,
            "career_id": attempt.get("career_id"),
            "position_id": attempt.get("position_id"),
            "company_id": attempt.get("company_id"),
            "status": attempt.get("status"),
            "created_at": attempt.get("created_at"),
            "scenario_version": attempt.get("scenario_version"),
            "public_scenario": attempt.get("public_scenario"),
        }
    )


@simulations_bp.route("/api/simulation/attempts/<attempt_id>/frontend/progress", methods=["GET", "POST"])
def frontend_workplace_progress(attempt_id):
    """Read or save validated progress for the signed-in attempt owner."""
    user_id = session.get("user_id")
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if (
        not attempt
        or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
        or attempt.get("position_id") != FRONTEND_DEVELOPER_POSITION_ID
        or not isinstance(attempt.get("public_scenario"), dict)
    ):
        return jsonify({"error": "Frontend simulation attempt not found."}), 404

    if request.method == "GET":
        return jsonify(
            get_frontend_workplace_progress(user_id=user_id, attempt_id=attempt_id)
        )

    payload = request.get_json(silent=True) or {}
    try:
        step = int(payload.get("step", 0))
        response = validate_frontend_progress(
            step=step,
            payload=payload.get("response", {}),
            existing_responses=attempt.get("responses", {}),
        )
        save_frontend_workplace_progress(
            user_id=user_id, attempt_id=attempt_id, step=step, response=response
        )
    except (TypeError, ValueError, FrontendProgressValidationError) as error:
        return jsonify({"error": str(error)}), 400
    result = {"saved": True, "step": step, "response": response}
    if step == WORKPLACE_FINAL_STEP:
        responses = dict(attempt.get("responses", {}))
        responses["step_5"] = response
        evaluation = evaluate_frontend_workplace_progress(responses)
        result["evaluation"] = save_simulation_evaluation(
            user_id=user_id, attempt_id=attempt_id, evaluation=evaluation
        )
    return jsonify(result)


@simulations_bp.post("/api/simulation/attempts/<attempt_id>/frontend/restart")
def restart_frontend_workplace(attempt_id):
    """Create a clean Frontend attempt while retaining previous attempt history."""
    user_id = session.get("user_id")
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if not attempt or attempt.get("position_id") != FRONTEND_DEVELOPER_POSITION_ID:
        return jsonify({"error": "Frontend simulation attempt not found."}), 404
    new_attempt_id = create_workplace_simulation_attempt(
        user_id=user_id,
        career_id=attempt.get("career_id"),
        position_id=FRONTEND_DEVELOPER_POSITION_ID,
        company_id=attempt.get("company_id"),
    )
    public = attempt.get("public_scenario", {})
    scenario, generation_count = generate_frontend_workplace_scenario(
        company_name=public.get("company_name") or attempt.get("company_id", "CareerGrid Company"),
        attempt_id=new_attempt_id,
    )
    save_workplace_scenario(
        user_id=user_id,
        attempt_id=new_attempt_id,
        public_scenario=scenario["public_scenario"],
        private_context=scenario["private_context"],
        generation_attempt_count=generation_count,
    )
    return jsonify(
        {
            "attempt_id": new_attempt_id,
            "workspace_url": url_for("simulations.workplace_attempt_workspace", attempt_id=new_attempt_id),
        }
    ), 201


@simulations_bp.post("/api/simulation/advisor/reply")
def simulation_advisor_reply():
    """Generate an advisor reply using owned attempt context when available."""
    payload = request.get_json(silent=True) or {}
    advisor_context = payload.get("advisor_context")

    if not isinstance(advisor_context, dict):
        return jsonify(
            {
                "error": "Advisor context is required.",
            }
        ), 400

    attempt_id = payload.get("attempt_id")

    if attempt_id:
        attempt = get_simulation_attempt(
            user_id=session.get("user_id"),
            attempt_id=str(attempt_id),
        )
        if (
            not attempt
            or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
            or not isinstance(attempt.get("public_scenario"), dict)
            or not isinstance(attempt.get("private_context"), dict)
        ):
            return jsonify({"error": "Simulation attempt not found."}), 404
        advisor_context = {
            "attempt": {
                "attempt_id": str(attempt_id),
                "career_id": attempt.get("career_id"),
                "position_id": attempt.get("position_id"),
                "company_id": attempt.get("company_id"),
                "public_scenario": attempt["public_scenario"],
            },
            "private_mentoring_context": attempt["private_context"],
            "user_visible_state": advisor_context,
        }

    try:
        reply = generate_advisor_reply(advisor_context)
    except AdvisorReplyError as error:
        current_app.logger.warning("Advisor reply generation failed: %s", error)
        return jsonify(
            {
                "error": "Advisor service is temporarily unavailable.",
            }
        ), 503

    return jsonify(reply)


@simulations_bp.post("/api/simulation/evaluation")
def simulation_workplace_evaluation():
    payload = request.get_json(silent=True) or {}
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        return jsonify({"error": "Evaluation evidence is required."}), 400
    attempt_id = payload.get("attempt_id")
    attempt = None
    if attempt_id:
        attempt = get_simulation_attempt(
            user_id=session.get("user_id"),
            attempt_id=str(attempt_id),
        )
        if (
            not attempt
            or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
            or not isinstance(attempt.get("public_scenario"), dict)
            or not isinstance(attempt.get("private_context"), dict)
        ):
            return jsonify({"error": "Simulation attempt not found."}), 404
        if isinstance(attempt.get("evaluation"), dict):
            return jsonify(get_user_visible_evaluation(attempt["evaluation"]) or {})
        evidence = {
            "attempt": {
                "attempt_id": str(attempt_id),
                "career_id": attempt.get("career_id"),
                "position_id": attempt.get("position_id"),
                "company_id": attempt.get("company_id"),
                "task": attempt["public_scenario"].get("task"),
                "skill_targets": attempt["public_scenario"].get("skill_targets", []),
            },
            "participant_context": {
                "student_display_name": str(session.get("user_name") or "").strip(),
                "advisor_name": str(
                    (attempt["public_scenario"].get("advisor") or {}).get("name")
                    or ""
                ).strip(),
            },
            "private_expected_solution": attempt["private_context"],
            "actual_user_evidence": evidence,
        }
    try:
        evaluation = evaluate_workplace_submission(evidence)
        if attempt_id and attempt:
            evaluation = save_simulation_evaluation(
                user_id=session.get("user_id"),
                attempt_id=str(attempt_id),
                evaluation=evaluation,
            )
        return jsonify(evaluation)
    except SimulationEvaluationError as error:
        current_app.logger.warning("Workplace evaluation failed: %s", error)
        return jsonify({"error": str(error)}), 503
