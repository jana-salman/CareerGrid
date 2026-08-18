from flask import Flask, jsonify, render_template, redirect, url_for, session, request
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from routes.auth import auth_bp

from services.evaluation_service import (
    SimulationEvaluationError,
    evaluate_workplace_submission,
    evaluate_frontend_workplace_progress,
)
from services.advisor_service import (
    AdvisorReplyError,
    generate_advisor_reply,
)
from services.scenario_generation_service import (
    ScenarioGenerationError,
    generate_workplace_scenario,
)
from services.frontend_workplace_scenario_service import (
    generate_frontend_workplace_scenario,
)
from services.simulation_storage import (
    save_simulation_evaluation,
    get_simulation_attempt,
    get_user_visible_evaluation,
    list_user_simulation_attempts,
    create_workplace_simulation_attempt,
    mark_workplace_generation_failed,
    save_workplace_scenario,
    save_frontend_workplace_progress,
    get_frontend_workplace_progress,
)
from services.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)

# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Create the Flask application
# ---------------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "careergrid-development-key"
)

app.register_blueprint(auth_bp)


# ---------------------------------------------------------
# Adzuna API configuration
# ---------------------------------------------------------

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")


# ---------------------------------------------------------
# Protect private pages
# ---------------------------------------------------------

PUBLIC_ROUTES = {
    "home",
    "auth.login",
    "auth.register",
    "auth.logout",
    "static"
}


@app.before_request
def protect_pages():
    """
    Redirect users to login when they try to open a private
    page without being authenticated.
    """

    if request.endpoint == "dashboard" and "user_id" not in session:
        return redirect(url_for("auth.login"))

    if (
        request.endpoint not in PUBLIC_ROUTES
        and "user_email" not in session
    ):
        return redirect(url_for("home"))

POSITIONS_DATA = {
    "software-developer": {

        "backend-developer": {
            "title": "Backend Developer",

            "companies": [
                {
                    "id": "technova",
                    "name": "TechNova",
                    "location": "Local"
                },

                {
                    "id": "brightsoft",
                    "name": "BrightSoft",
                    "location": "Global"
                }
            ]
        },

        "frontend-developer": {
            "title": "Frontend Developer",

            "companies": [
                {
                    "id": "pixelworks",
                    "name": "PixelWorks",
                    "location": "Local"
                },

                {
                    "id": "cloudbyte",
                    "name": "CloudByte",
                    "location": "Global"
                }
            ]
        }
    },

    "ui-ux-designer": {

        "ux-designer": {
            "title": "UX Designer",

            "companies": [
                {
                    "id": "designflow",
                    "name": "DesignFlow",
                    "location": "Local"
                },

                {
                    "id": "nexora",
                    "name": "Nexora",
                    "location": "Global"
                }
            ]
        },

        "ui-designer": {
            "title": "UI Designer",

            "companies": [
                {
                    "id": "pixelcraft",
                    "name": "PixelCraft",
                    "location": "Local"
                },

                {
                    "id": "visionlabs",
                    "name": "VisionLabs",
                    "location": "Global"
                }
            ]
        }
    },

    "data-analyst": {

        "data-analyst": {
            "title": "Data Analyst",

            "companies": [
                {
                    "id": "insightlab",
                    "name": "InsightLab",
                    "location": "Local"
                },

                {
                    "id": "datapulse",
                    "name": "DataPulse",
                    "location": "Global"
                }
            ]
        }
    }
    
}


# =========================================================
# ADZUNA JOB API
# =========================================================

def fetch_adzuna_jobs(job_title, location="", results=5):
    """
    Retrieve job listings from Adzuna.

    If the API credentials are missing or the request fails,
    return an empty list instead of crashing the website.
    """

    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []

    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": job_title,
        "where": location,
        "results_per_page": results,
        "content-type": "application/json"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        return data.get("results", [])

    except requests.exceptions.RequestException as error:
        print("Adzuna API error:", error)
        return []


# =========================================================
# MAIN WEBSITE ROUTES
# =========================================================

@app.route("/")
def home():
    return redirect(url_for("auth.login"))


@app.route("/career")
def career():
    return render_template(
        "career.html",
        user_name=session.get("user_name")
    )


@app.route("/positions/<career_id>")
def positions(career_id):
    career_name = career_id.replace("-", " ").title()

    position_data = POSITIONS_DATA.get(
        career_id,
        {}
    )

    return render_template(
        "positions.html",
        career_id=career_id,
        career_name=career_name,
        positions=position_data
    )


@app.route("/positions/<career_id>/<position_id>")
def companies(career_id, position_id):
    career_name = career_id.replace("-", " ").title()

    position_data = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    position_title = position_data.get("title", "")
    local_companies = position_data.get("companies", [])

    jobs = fetch_adzuna_jobs(
    position_title,
    results=5
)  # Live jobs disabled

    return render_template(
        "companies.html",
        career_id=career_id,
        career_name=career_name,
        position_id=position_id,
        position_title=position_title,
        jobs=jobs,
        local_companies=local_companies
    )


@app.route("/workspace/<career_id>/<position_id>/<company_id>")
def simulation_workspace(career_id, position_id, company_id):
    """
    Display the persistent desktop workspace for a simulation.
    """

    position_data = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    # Invalid career/position.
    if not position_data:
        return redirect(
            url_for(
                "positions",
                career_id=career_id
            )
        )

    position_title = position_data.get(
        "title",
        position_id.replace("-", " ").title()
    )

    # Default company name for live Adzuna listings.
    company_name = company_id.replace("-", " ").title()

    # If this is one of our local/demo companies,
    # use its proper display name.
    for company in position_data.get("companies", []):
        if company.get("id") == company_id:
            company_name = company.get(
                "name",
                company_name
            )
            break

    return render_template(
        "desktop.html",
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        career_name=career_id.replace("-", " ").title(),
        position_title=position_title,
        company_name=company_name,
        user_name=session.get("user_name", "User")
    )

@app.post("/simulation/workplace/start")
def start_workplace_simulation():
    career_id = request.form.get("career_id", "").strip()
    position_id = request.form.get("position_id", "").strip()
    company_id = request.form.get("company_id", "").strip()
    job_source = request.form.get("job_source", "demo").strip().lower()

    position = POSITIONS_DATA.get(career_id, {}).get(position_id)

    if not position:
        return redirect(url_for("career"))

    if job_source == "adzuna":
        # Live Adzuna jobs use the company name.
        if not company_id or len(company_id) > 200:
            return redirect(
                url_for(
                    "companies",
                    career_id=career_id,
                    position_id=position_id
                )
            )

    else:
        # Demo companies must match the IDs in POSITIONS_DATA.
        valid_companies = {
            company.get("id")
            for company in position.get("companies", [])
        }

        if company_id not in valid_companies:
            return redirect(
                url_for(
                    "companies",
                    career_id=career_id,
                    position_id=position_id
                )
            )

    attempt_id = None
    workplace_stage = "attempt_creation"
    try:
        attempt_id = create_workplace_simulation_attempt(user_id=session.get("user_id"), career_id=career_id, position_id=position_id, company_id=company_id)
        app.logger.info("Created workplace simulation attempt %s (%s/%s/%s)", attempt_id, career_id, position_id, company_id)
        workplace_stage = "frontend_scenario_generation" if position_id == "frontend-developer" else "scenario_generation"
        if position_id == "frontend-developer":
            company_name = next(
                (
                    company.get("name")
                    for company in position.get("companies", [])
                    if company.get("id") == company_id
                ),
                company_id,
            )
            scenario, generation_attempt_count = (
                generate_frontend_workplace_scenario(
                    company_name=company_name,
                    attempt_id=attempt_id,
                )
            )
        else:
            scenario, generation_attempt_count = generate_workplace_scenario(
                career_id=career_id,
                position_id=position_id,
                company_id=company_id,
                attempt_id=attempt_id,
            )
        workplace_stage = "firebase_scenario_storage"
        save_workplace_scenario(
            user_id=session.get("user_id"),
            attempt_id=attempt_id,
            public_scenario=scenario["public_scenario"],
            private_context=scenario["private_context"],
            generation_attempt_count=generation_attempt_count,
        )
        app.logger.info("Scenario generation completed for workplace attempt %s", attempt_id)
    except ScenarioGenerationError:
        app.logger.warning("Scenario generation failed for workplace attempt %s", attempt_id)
        try:
            mark_workplace_generation_failed(user_id=session.get("user_id"), attempt_id=attempt_id)
        except Exception:
            app.logger.exception("Could not mark workplace generation as failed")
        return redirect(url_for("workplace_attempt_workspace", attempt_id=attempt_id))
    except Exception as error:
        app.logger.exception(
            "Workplace attempt failed: type=%s message=%s attempt_id=%s career_id=%s position_id=%s stage=%s",
            type(error).__name__, error, attempt_id, career_id, position_id, workplace_stage,
        )
        if attempt_id:
            try:
                mark_workplace_generation_failed(
                    user_id=session.get("user_id"),
                    attempt_id=attempt_id,
                )
            except Exception:
                app.logger.exception("Could not mark workplace generation as failed")
            return redirect(url_for("workplace_attempt_workspace", attempt_id=attempt_id))
        return redirect(url_for("companies", career_id=career_id, position_id=position_id))
    return redirect(url_for("workplace_attempt_workspace", attempt_id=attempt_id))


@app.get("/workspace/attempt/<attempt_id>")
def workplace_attempt_workspace(attempt_id):
    attempt = get_simulation_attempt(user_id=session.get("user_id"), attempt_id=attempt_id)
    if not attempt or attempt.get("simulation_mode") != "workplace":
        return redirect(url_for("career"))
    career_id, position_id, company_id = attempt.get("career_id"), attempt.get("position_id"), attempt.get("company_id")
    if attempt.get("status") in {"generation_failed", "generating"}:
        return render_template(
            "simulation_generation_failed.html",
            career_id=career_id,
            position_id=position_id,
            generation_pending=attempt.get("status") == "generating",
        )
    position = POSITIONS_DATA.get(career_id, {}).get(position_id)
    if not position:
        return redirect(url_for("career"))
    company_name = next((company.get("name") for company in position.get("companies", []) if company.get("id") == company_id), company_id.replace("-", " ").title())
    return render_template("desktop.html", attempt_id=attempt_id, career_id=career_id, position_id=position_id, company_id=company_id, career_name=career_id.replace("-", " ").title(), position_title=position.get("title", position_id.replace("-", " ").title()), company_name=company_name, user_name=session.get("user_name", "User"))


@app.get("/api/simulation/attempts/<attempt_id>")
def get_public_workplace_attempt(attempt_id):
    """Return only browser-safe scenario data for the signed-in user."""
    attempt = get_simulation_attempt(
        user_id=session.get("user_id"),
        attempt_id=attempt_id,
    )
    if not attempt or attempt.get("simulation_mode") != "workplace":
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


@app.route("/api/simulation/attempts/<attempt_id>/frontend/progress", methods=["GET", "POST"])
def frontend_workplace_progress(attempt_id):
    """Read or save validated progress for the signed-in attempt owner."""
    user_id = session.get("user_id")
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if (
        not attempt
        or attempt.get("simulation_mode") != "workplace"
        or attempt.get("position_id") != "frontend-developer"
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
    if step == 5:
        responses = dict(attempt.get("responses", {}))
        responses["step_5"] = response
        evaluation = evaluate_frontend_workplace_progress(responses)
        result["evaluation"] = save_simulation_evaluation(
            user_id=user_id, attempt_id=attempt_id, evaluation=evaluation
        )
    return jsonify(result)


@app.post("/api/simulation/attempts/<attempt_id>/frontend/restart")
def restart_frontend_workplace(attempt_id):
    """Create a clean Frontend attempt while retaining previous attempt history."""
    user_id = session.get("user_id")
    attempt = get_simulation_attempt(user_id=user_id, attempt_id=attempt_id)
    if not attempt or attempt.get("position_id") != "frontend-developer":
        return jsonify({"error": "Frontend simulation attempt not found."}), 404
    new_attempt_id = create_workplace_simulation_attempt(
        user_id=user_id,
        career_id=attempt.get("career_id"),
        position_id="frontend-developer",
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
            "workspace_url": url_for("workplace_attempt_workspace", attempt_id=new_attempt_id),
        }
    ), 201


@app.post("/api/simulation/advisor/reply")
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
            or attempt.get("simulation_mode") != "workplace"
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
        app.logger.warning("Advisor reply generation failed: %s", error)
        return jsonify(
            {
                "error": "Advisor service is temporarily unavailable.",
            }
        ), 503

    return jsonify(reply)


@app.post("/api/simulation/evaluation")
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
            or attempt.get("simulation_mode") != "workplace"
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
        app.logger.warning("Workplace evaluation failed: %s", error)
        return jsonify({"error": str(error)}), 503


# =========================================================
# DASHBOARD HELPERS
# =========================================================

def _lookup_position_title(career_id, position_id):
    """Return the readable position title."""

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    title = position.get("title")

    if title:
        return title

    if position_id:
        return position_id.replace("-", " ").title()

    return "Simulation"


def _lookup_career_name(career_id):
    """Return the readable career name used by selection pages."""
    career_names = {
        "software-developer": "Software Developer",
        "ui-ux-designer": "UI/UX Designer",
        "data-analyst": "Data Analyst",
    }
    if career_id in career_names:
        return career_names[career_id]
    if career_id:
        return str(career_id).replace("-", " ").title()
    return "Career"


def _lookup_company_name(career_id, position_id, company_id):
    """Return the readable company name."""

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    for company in position.get("companies", []):
        if company.get("id") == company_id:
            return company.get("name", company_id)

    if company_id:
        return company_id.replace("-", " ").title()

    return "Company"


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
        "career_name": _lookup_career_name(career_id),
        "position_title": _lookup_position_title(
            career_id,
            position_id,
        ),
        "company_name": _lookup_company_name(
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
            and summary.get("simulation_mode") == "workplace"
        ),
    }


# =========================================================
# DASHBOARD ROUTES
# =========================================================

@app.route("/dashboard")
def dashboard():
    """Show the signed-in user's Firebase simulation history."""

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    summaries = [
        summary
        for summary in list_user_simulation_attempts(user_id)
        if summary.get("simulation_mode") == "workplace"
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


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
    