"""Workplace simulation pages, reports, and JSON API routes."""

import json
import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from constants import (
    FRONTEND_DEVELOPER_POSITION_ID,
    MAX_EVALUATION_EVIDENCE_CHARS,
    MAX_EVALUATION_FILES,
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
    get_backend_fallback_scenario,
    is_backend_demo,
)
from services.ai.evaluation_service import (
    SimulationEvaluationError,
    evaluate_frontend_workplace_progress,
    evaluate_workplace_submission,
    normalize_review_items,
)
from services.ai.roadmap import normalize_report_evaluation
from services.simulation.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)
from services.simulation.frontend_workplace_scenario_service import (
    deterministic_frontend_scenario,
    generate_frontend_workplace_scenario,
)
from ai_prompt.prompts.scenario_v5 import SCENARIO_PROMPT_VERSION
from services.ai.generation_runtime import GenerationReport
from services.simulation.assignment_library import (
    GenerationResult,
    assignment_identity,
    obtain_assignment,
)
from services.simulation.job_context_service import (
    LIVE_SOURCES,
    build_catalog_job_context,
    JobContextError,
    build_job_context,
    simulation_notice,
)
from services.ai.scenario_generation_service import ScenarioGenerationError, generate_workplace_scenario
from services.simulation.simulation_storage import (
    create_workplace_simulation_attempt,
    get_frontend_workplace_progress,
    get_simulation_attempt,
    get_user_visible_evaluation,
    mark_workplace_generation_failed,
    restart_workplace_generation,
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

    invalid = url_for(
        "careers.companies",
        career_id=career_id,
        position_id=position_id,
    )
    if job_source == BACKEND_DEMO_JOB_SOURCE:
        if not is_backend_demo(career_id, position_id, company_id):
            return invalid
    elif job_source in LIVE_SOURCES:
        # Live listings use the company name.
        if (
            not company_id
            or len(company_id) > current_app.config["MAX_ADZUNA_COMPANY_NAME_LENGTH"]
        ):
            return invalid
    else:
        # Demo companies must match the IDs in POSITIONS_DATA.
        valid_companies = {
            company.get("id")
            for company in position.get("companies", [])
        }

        if company_id not in valid_companies:
            return invalid

    return None


def _company_name_for(position: dict, company_id: str, job_context: dict | None) -> str:
    if job_context and job_context.get("company"):
        return job_context["company"]
    return next(
        (
            company.get("name")
            for company in position.get("companies", [])
            if company.get("id") == company_id
        ),
        company_id,
    )


def _fallback_scenario(position_id: str, company_name: str, attempt_id: str) -> dict:
    """The validated built-in assignment for this role (never cached as generated)."""

    if position_id == FRONTEND_DEVELOPER_POSITION_ID:
        return deterministic_frontend_scenario(company_name, attempt_id)
    return get_backend_fallback_scenario(attempt_id=attempt_id)


def _assignment_generator(
    *, career_id: str, position_id: str, company_id: str, company_name: str, job_context: dict | None
):
    """Return generate(scenario_id) -> GenerationResult for the assignment library."""

    def generate(scenario_id: str) -> GenerationResult:
        report = GenerationReport()
        try:
            if position_id == FRONTEND_DEVELOPER_POSITION_ID:
                scenario, count = generate_frontend_workplace_scenario(
                    company_name=company_name,
                    attempt_id=scenario_id,
                    job_context=job_context,
                    report=report,
                )
                if not count:  # the generator returned its own built-in fallback
                    scenario = None
            else:
                scenario, count = generate_workplace_scenario(
                    career_id=career_id,
                    position_id=position_id,
                    company_id=company_id,
                    attempt_id=scenario_id,
                    company_name=company_name,
                    job_context=job_context,
                    report=report,
                )
        except ScenarioGenerationError:
            scenario, count = None, 0
        details = report.to_record()
        details["prompt_version"] = details.get("prompt_version") or SCENARIO_PROMPT_VERSION
        if scenario is None:
            return GenerationResult(None, 0, details, report.failure_reason or "generation_error")
        return GenerationResult(scenario, count, details)

    return generate


def _generate_simulation_scenario(
    *,
    career_id: str,
    position_id: str,
    company_id: str,
    attempt_id: str,
    position: dict,
    is_backend_demo_request: bool,
    job_context: dict | None = None,
    user_id: str | None = None,
) -> tuple[dict, int, str, dict]:
    """
    Return the workplace scenario for the given attempt.

    The company/position (or listing/position) has one saved assignment: the
    first launch generates and validates it, later launches copy it without a
    Gemini call. Returns (scenario, generation_attempt_count,
    generation_source, details); ``details`` are internal diagnostics stored
    with the attempt. Failures use the validated built-in assignment.
    """

    _ = user_id  # assignments are shared per role, not per user
    company_name = _company_name_for(position, company_id, job_context)
    if job_context is None and not is_backend_demo_request:
        # Practice companies have a defined role profile instead of a listing.
        job_context = build_catalog_job_context(position_id, company_id)
    if is_backend_demo_request:
        scenario = get_backend_demo_workplace_scenario(attempt_id=attempt_id)
        generation_attempt_count = 1
        generation_source = "predefined_demo"
        report = GenerationReport()
        report.finish("predefined_demo")
        details = report.to_record()
    else:
        identity = assignment_identity(
            career_id=career_id, position_id=position_id, company_id=company_id, job_context=job_context
        )
        outcome = obtain_assignment(
            identity=identity,
            job_context=job_context,
            generate=_assignment_generator(
                career_id=career_id, position_id=position_id, company_id=company_id,
                company_name=company_name, job_context=job_context,
            ),
            fallback=lambda: _fallback_scenario(position_id, company_name, attempt_id),
        )
        scenario = outcome.scenario
        generation_attempt_count = outcome.generation_count
        generation_source = "fallback" if outcome.is_fallback else "gemini"
        details = {
            **outcome.details,
            "assignment_key": outcome.key,
            "assignment_version": outcome.version,
            "assignment_source": outcome.source,
        }
        if outcome.is_fallback:
            details["outcome"] = "fallback"
            details["failure_reason"] = details.get("failure_reason") or outcome.reason
            current_app.logger.warning(
                "Using the built-in assignment for attempt %s (%s)", attempt_id, outcome.reason
            )

    public = scenario.get("public_scenario")
    if isinstance(public, dict) and generation_source != "predefined_demo":
        # Server-written notice, so generated text cannot blur simulation
        # and real employer assignments.
        public["simulation_notice"] = simulation_notice(
            job_context, fallback=generation_source == "fallback"
        )
        if job_context:
            public["job_context"] = {
                key: job_context.get(key, "")
                for key in ("title", "company", "location", "source", "source_label", "url")
            }
    details["prompt_version"] = details.get("prompt_version") or SCENARIO_PROMPT_VERSION
    return scenario, generation_attempt_count, generation_source, details


def _start_retry_attempt(user_id: str, source: dict, source_attempt_id: str) -> str:
    """A clean attempt with the same assignment as ``source`` (no Gemini call).

    The new attempt gets its own copy, so its workspace, submission, feedback,
    and roadmap are independent of the earlier attempt.
    """

    new_attempt_id = create_workplace_simulation_attempt(
        user_id=user_id,
        career_id=source.get("career_id"),
        position_id=source.get("position_id"),
        company_id=source.get("company_id"),
        job_context=source.get("job_context") if isinstance(source.get("job_context"), dict) else None,
    )
    generation = source.get("generation") if isinstance(source.get("generation"), dict) else {}
    save_workplace_scenario(
        user_id=user_id,
        attempt_id=new_attempt_id,
        public_scenario=source["public_scenario"],
        private_context=source["private_context"],
        generation_attempt_count=0,
        generation_source=str(generation.get("source") or "gemini"),
        generation_details={
            key: generation[key]
            for key in ("assignment_key", "assignment_version", "assignment_source", "prompt_version", "model")
            if key in generation
        } | {"reused_from_attempt": source_attempt_id, "outcome": "reused"},
    )
    return new_attempt_id


def _retryable_source(user_id: str, attempt_id: str) -> dict | None:
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if (
        not attempt
        or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
        or not isinstance(attempt.get("public_scenario"), dict)
        or not isinstance(attempt.get("private_context"), dict)
    ):
        return None
    return attempt


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
        _mark_failed(user_id, attempt_id)
        return url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id)

    return url_for(
        "careers.companies",
        career_id=career_id,
        position_id=position_id,
    )


def _mark_failed(user_id: str, attempt_id: str) -> None:
    try:
        mark_workplace_generation_failed(
            user_id=user_id,
            attempt_id=attempt_id,
        )
    except Exception:
        current_app.logger.exception("Could not mark workplace generation as failed")


def _run_generation(
    *,
    user_id: str,
    attempt_id: str,
    career_id: str,
    position_id: str,
    company_id: str,
    position: dict,
    is_backend_demo_request: bool,
    job_context: dict | None,
) -> bool:
    """Generate and persist the scenario once. Returns True on success."""

    workplace_stage = (
        "predefined_demo_scenario"
        if is_backend_demo_request
        else "frontend_scenario_generation"
        if position_id == FRONTEND_DEVELOPER_POSITION_ID
        else "scenario_generation"
    )
    try:
        scenario, generation_attempt_count, generation_source, details = _generate_simulation_scenario(
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            attempt_id=attempt_id,
            position=position,
            is_backend_demo_request=is_backend_demo_request,
            job_context=job_context,
            user_id=user_id,
        )
        workplace_stage = "firebase_scenario_storage"
        save_workplace_scenario(
            user_id=user_id,
            attempt_id=attempt_id,
            public_scenario=scenario["public_scenario"],
            private_context=scenario["private_context"],
            generation_attempt_count=generation_attempt_count,
            generation_source=generation_source,
            generation_details=details,
        )
        current_app.logger.info(
            "Workplace task for attempt %s: source=%s outcome=%s reason=%s seconds=%s",
            attempt_id, generation_source, details.get("outcome"),
            details.get("failure_reason") or "-", details.get("duration_seconds"),
        )
    except ScenarioGenerationError:
        current_app.logger.warning(
            "Scenario generation failed for workplace attempt %s",
            attempt_id,
        )
        return False
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
        return False
    current_app.logger.info(
        "Scenario generation completed for workplace attempt %s",
        attempt_id,
    )
    return True


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

    retry_attempt_id = request.form.get("retry_attempt_id", "").strip()
    if retry_attempt_id:
        source = _retryable_source(session.get("user_id"), retry_attempt_id)
        if source and source.get("career_id") == career_id and source.get("position_id") == position_id:
            try:
                new_attempt_id = _start_retry_attempt(session.get("user_id"), source, retry_attempt_id)
            except Exception:
                current_app.logger.exception("Could not start a retry attempt")
            else:
                return redirect(url_for("simulations.workplace_attempt_workspace", attempt_id=new_attempt_id))

    invalid_company_redirect = _validate_simulation_company(
        career_id, position_id, company_id, job_source, position
    )
    if invalid_company_redirect:
        return redirect(invalid_company_redirect)

    attempt_id = None
    try:
        attempt_id = create_workplace_simulation_attempt(
            user_id=session.get("user_id"),
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
        )
    except Exception as error:
        current_app.logger.exception(
            "Workplace attempt failed: type=%s attempt_id=%s career_id=%s "
            "position_id=%s stage=%s",
            type(error).__name__, attempt_id, career_id, position_id, "attempt_creation",
        )
    else:
        current_app.logger.info(
            "Created workplace simulation attempt %s (%s/%s/%s)",
            attempt_id, career_id, position_id, company_id,
        )
        if _run_generation(
            user_id=session.get("user_id"),
            attempt_id=attempt_id,
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            position=position,
            is_backend_demo_request=is_backend_demo_request,
            job_context=None,
        ):
            return redirect(url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id))

    return redirect(
        _handle_generation_failure(
            user_id=session.get("user_id"),
            attempt_id=attempt_id,
            career_id=career_id,
            position_id=position_id,
        )
    )


START_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
START_REQUESTS_SESSION_KEY = "workplace_start_requests"
MAX_REMEMBERED_START_REQUESTS = 10
STALE_GENERATION_SECONDS = 420  # longer than the maximum generation budget plus storage


def _generation_is_stale(attempt: dict) -> bool:
    stamp = attempt.get("updated_at") or attempt.get("created_at")
    try:
        started = datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return True
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - started).total_seconds() > STALE_GENERATION_SECONDS


def _remember_start_request(request_id: str, attempt_id: str) -> None:
    remembered = dict(session.get(START_REQUESTS_SESSION_KEY) or {})
    remembered[request_id] = attempt_id
    session[START_REQUESTS_SESSION_KEY] = dict(
        list(remembered.items())[-MAX_REMEMBERED_START_REQUESTS:]
    )


def _start_error(message: str, status: int, *, retryable: bool = False, **extra):
    return jsonify({"error": message, "retryable": retryable, **extra}), status


@simulations_bp.post("/api/simulation/workplace/start")
def start_workplace_simulation_api():
    """Create (or resume) one attempt and generate its task.

    The browser sends a ``client_request_id`` that stays the same across
    retries of one selection, so a retry reuses the same attempt instead of
    creating duplicates.
    """

    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}
    career_id = str(payload.get("career_id") or "").strip()
    position_id = str(payload.get("position_id") or "").strip()
    company_id = str(payload.get("company_id") or "").strip()
    job_source = str(payload.get("job_source") or "demo").strip().lower()
    request_id = str(payload.get("client_request_id") or "").strip()

    if not START_REQUEST_ID_PATTERN.fullmatch(request_id):
        return _start_error("A valid request identifier is required.", 400)
    position = POSITIONS_DATA.get(career_id, {}).get(position_id)
    if not position or not is_position_available(career_id, position_id):
        return _start_error("This career path is not available.", 404)
    if _validate_simulation_company(career_id, position_id, company_id, job_source, position):
        return _start_error("Choose a company or listing from the list.", 400)
    try:
        job_context = build_job_context(job_source, payload.get("job_context"))
    except JobContextError as error:
        return _start_error(str(error), 400)
    is_backend_demo_request = job_source == BACKEND_DEMO_JOB_SOURCE and is_backend_demo(
        career_id, position_id, company_id
    )

    attempt_id = (session.get(START_REQUESTS_SESSION_KEY) or {}).get(request_id)
    if attempt_id:
        existing = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
        status = (existing or {}).get("status")
        if existing and existing.get("public_scenario"):
            # Generate once per attempt: reuse the saved task.
            return jsonify({
                "attempt_id": attempt_id,
                "reused": True,
                "workspace_url": url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id),
            })
        if status == "generating" and not _generation_is_stale(existing):
            return _start_error(
                "Your workspace is still being prepared. Please wait a moment and try again.",
                409, retryable=True,
            )
        if existing:
            try:
                restart_workplace_generation(user_id=user_id, attempt_id=attempt_id)
            except Exception:
                current_app.logger.exception("Could not restart workplace generation")
                attempt_id = None
        else:
            attempt_id = None

    if not attempt_id:
        try:
            attempt_id = create_workplace_simulation_attempt(
                user_id=user_id,
                career_id=career_id,
                position_id=position_id,
                company_id=company_id,
                job_context=job_context,
            )
        except Exception as error:
            current_app.logger.exception(
                "Workplace attempt creation failed: type=%s", type(error).__name__
            )
            return _start_error(
                "CareerGrid could not create your workspace. Please try again.",
                503, retryable=True,
            )
        _remember_start_request(request_id, attempt_id)

    if _run_generation(
        user_id=user_id,
        attempt_id=attempt_id,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        position=position,
        is_backend_demo_request=is_backend_demo_request,
        job_context=job_context,
    ):
        return jsonify({
            "attempt_id": attempt_id,
            "reused": False,
            "workspace_url": url_for("simulations.workplace_attempt_workspace", attempt_id=attempt_id),
        }), 201

    _mark_failed(user_id, attempt_id)
    return _start_error(
        "We couldn't generate a task for this path right now. Your selection is "
        "saved, so you can try again.",
        503, retryable=True, attempt_id=attempt_id,
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
    # Older reports may hold roadmap objects stored as text; recover them for
    # display (literals only, never executed) without changing the record.
    evaluation = normalize_report_evaluation(evaluation)

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
    elif isinstance(attempt.get("job_context"), dict) and attempt["job_context"].get("source"):
        job_source = attempt["job_context"]["source"]
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
        private_context = attempt.get("private_context") or {}
        project = attempt["public_scenario"].get("project") or {}
        patch_checks = private_context.get("patch_checks") if isinstance(private_context, dict) else None
        response = validate_frontend_progress(
            step=step,
            payload=payload.get("response", {}),
            existing_responses=attempt.get("responses", {}),
            patch_checks=patch_checks or None,
            project_files={
                str(item.get("path")): str(item.get("content", ""))
                for item in project.get("files", [])
                if isinstance(item, dict) and item.get("path")
            } if patch_checks else None,
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
        evaluation = evaluate_frontend_workplace_progress(
            responses, private_context=attempt.get("private_context") or {}
        )
        result["evaluation"] = save_simulation_evaluation(
            user_id=user_id, attempt_id=attempt_id, evaluation=evaluation
        )
    return jsonify(result)


@simulations_bp.post("/api/simulation/attempts/<attempt_id>/frontend/restart")
def restart_frontend_workplace(attempt_id):
    """Create a clean Frontend attempt with the same assignment, keeping history."""
    user_id = session.get("user_id")
    attempt = _retryable_source(user_id, attempt_id)
    if not attempt or attempt.get("position_id") != FRONTEND_DEVELOPER_POSITION_ID:
        return jsonify({"error": "Frontend simulation attempt not found."}), 404
    return _retry_response(user_id, attempt, attempt_id)


@simulations_bp.post("/api/simulation/attempts/<attempt_id>/retry")
def retry_workplace_attempt(attempt_id):
    """Start a clean attempt with the same saved assignment (no Gemini call)."""
    user_id = session.get("user_id")
    attempt = _retryable_source(user_id, attempt_id)
    if not attempt:
        return jsonify({"error": "Simulation attempt not found."}), 404
    return _retry_response(user_id, attempt, attempt_id)


def _retry_response(user_id: str, attempt: dict, attempt_id: str):
    try:
        new_attempt_id = _start_retry_attempt(user_id, attempt, attempt_id)
    except Exception:
        current_app.logger.exception("Could not start a retry attempt")
        return jsonify({"error": "CareerGrid could not start a new attempt. Please try again.", "retryable": True}), 503
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
    changed_files = evidence.get("changed_files")
    if changed_files is not None and (
        not isinstance(changed_files, list) or len(changed_files) > MAX_EVALUATION_FILES
    ):
        return jsonify({"error": "Evaluation evidence is malformed."}), 400
    if len(json.dumps(evidence, ensure_ascii=False)) > MAX_EVALUATION_EVIDENCE_CHARS:
        return jsonify({"error": "The submission is too large to evaluate."}), 413
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
    if isinstance(changed_files, list) and not changed_files:
        return jsonify(
            {"error": "The submission has no changes compared with the original project."}
        ), 400
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
