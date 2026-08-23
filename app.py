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
from services.backend_demo_scenario_service import (
    BACKEND_DEMO_CAREER_ID,
    BACKEND_DEMO_COMPANY_NAME,
    BACKEND_DEMO_JOB_SOURCE,
    BACKEND_DEMO_POSITION_ID,
    get_backend_demo_job,
    get_backend_demo_workplace_scenario,
    is_backend_demo,
)
from services.backend_demo_interview_service import (
    get_backend_demo_interview,
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

    create_interview_attempt,
    get_interview_attempt,
    save_interview_answer,
    complete_interview_attempt,
)

from services.interview_service import (
    InterviewGenerationError,
    InterviewEvaluationError,
    generate_interview_questions,
    analyze_spoken_answer,
    generate_final_interview_evaluation,
)

from services.frontend_workplace_progress_service import (
    FrontendProgressValidationError,
    validate_frontend_progress,
)

from services.interview_service import (
    InterviewGenerationError,
    InterviewEvaluationError,
    generate_interview_questions,
    analyze_spoken_answer,
    generate_final_interview_evaluation,
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


def _company_display_name(career_id, position_id, company_id):
    """Resolve a stable user-facing company name for all attempt pages."""

    if is_backend_demo(career_id, position_id, company_id):
        return BACKEND_DEMO_COMPANY_NAME

    position = POSITIONS_DATA.get(career_id, {}).get(position_id, {})

    for company in position.get("companies", []):
        if company.get("id") == company_id:
            return company.get("name", company_id)

    if company_id:
        return company_id.replace("-", " ").title()

    return "Company"


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
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "home.html",
        user_name=session.get("user_name")
    )


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

    demo_job = None
    if (
        career_id == BACKEND_DEMO_CAREER_ID
        and position_id == BACKEND_DEMO_POSITION_ID
    ):
        demo_job = get_backend_demo_job()

    return render_template(
        "companies.html",
        career_id=career_id,
        career_name=career_name,
        position_id=position_id,
        position_title=position_title,
        jobs=jobs,
        local_companies=local_companies,
        demo_job=demo_job,
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

    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )

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
    is_backend_demo_request = (
        job_source == BACKEND_DEMO_JOB_SOURCE
        and is_backend_demo(career_id, position_id, company_id)
    )

    position = POSITIONS_DATA.get(career_id, {}).get(position_id)

    if not position:
        return redirect(url_for("career"))

    if job_source == BACKEND_DEMO_JOB_SOURCE:
        if not is_backend_demo(career_id, position_id, company_id):
            return redirect(
                url_for(
                    "companies",
                    career_id=career_id,
                    position_id=position_id,
                )
            )
    elif job_source == "adzuna":
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
        generation_source = "gemini"
        workplace_stage = "frontend_scenario_generation" if position_id == "frontend-developer" else "scenario_generation"
        if is_backend_demo_request:
            workplace_stage = "predefined_demo_scenario"
            scenario = get_backend_demo_workplace_scenario(
                attempt_id=attempt_id,
            )
            generation_attempt_count = 1
            generation_source = "predefined_demo"
        elif position_id == "frontend-developer":
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
            generation_source=generation_source,
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
    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )
    return render_template("desktop.html", attempt_id=attempt_id, career_id=career_id, position_id=position_id, company_id=company_id, career_name=career_id.replace("-", " ").title(), position_title=position.get("title", position_id.replace("-", " ").title()), company_name=company_name, user_name=session.get("user_name", "User"))
def normalize_review_items(value):
    """
    Normalize an evaluation field into a clean list of strings.

    Gemini/evaluation data may contain either:
    - a list of strings
    - one plain string
    - no value
    """

    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        return [value]

    return [str(value).strip()]
@app.get("/simulation/attempts/<attempt_id>/report")
def workplace_task_review(attempt_id):
    """
    Display the final persisted review for a completed
    workplace simulation attempt.
    """

    user_id = session.get("user_id")

    attempt = get_simulation_attempt(
        user_id=user_id,
        attempt_id=attempt_id,
    )

    if (
        not attempt
        or attempt.get("simulation_mode") != "workplace"
    ):
        return redirect(
            url_for("career")
        )


    evaluation = get_user_visible_evaluation(
        attempt.get("evaluation")
    )

    strengths = normalize_review_items(
    evaluation.get("strengths")
)

    areas_for_improvement = normalize_review_items(
        evaluation.get("areas_for_improvement")
    )

    recommended_next_steps = normalize_review_items(
        evaluation.get("recommended_next_steps")
        or evaluation.get("recommended_skills")
    )
    
    if not evaluation:
        return redirect(
            url_for(
                "workplace_attempt_workspace",
                attempt_id=attempt_id,
            )
        )


    career_id = attempt.get(
        "career_id",
        ""
    )

    position_id = attempt.get(
        "position_id",
        ""
    )

    company_id = attempt.get(
        "company_id",
        ""
    )


    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )


    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " "
        ).title(),
    )


    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )

    valid_demo_company_ids = set()

    for company in position.get(
        "companies",
        []
    ):
        company_value = company.get("id")

        if company_value:
            valid_demo_company_ids.add(
                company_value
            )

        if company_value == company_id:
            company_name = company.get(
                "name",
                company_name,
            )


    if is_backend_demo(career_id, position_id, company_id):
        job_source = BACKEND_DEMO_JOB_SOURCE
    else:
        job_source = (
            "demo"
            if company_id in valid_demo_company_ids
            else "adzuna"
        )


    public_scenario = attempt.get(
        "public_scenario",
        {}
    )

    task = (
        public_scenario.get(
            "task",
            {}
        )
        if isinstance(
            public_scenario,
            dict,
        )
        else {}
    )


    task_title = (
        task.get("subject")
        or task.get("title")
        or "Workplace Task Review"
    )

        # --------------------------------------------------------
    # Interview simulation unlock
    # --------------------------------------------------------

    overall_score = evaluation.get("overall_score", 0)

    try:
        overall_score = float(overall_score)
    except (TypeError, ValueError):
        overall_score = 0

    interview_unlocked = overall_score >= 85


    return render_template(
        "task_review.html",
        attempt_id=attempt_id,
        evaluation=evaluation,
        task_title=task_title,
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        position_title=position_title,
        company_name=company_name,
        job_source=job_source,
        strengths=strengths,
        areas_for_improvement=areas_for_improvement,
        recommended_next_steps=recommended_next_steps,
        interview_unlocked=interview_unlocked,
    )
@app.post("/simulation/attempts/<attempt_id>/interview/start")
def start_interview(attempt_id):
    """
    Start a fresh interview from a completed workplace simulation.
    """

    user_id = session.get("user_id")

    attempt = get_simulation_attempt(
        user_id=user_id,
        attempt_id=attempt_id,
    )

    if (
        not attempt
        or attempt.get("simulation_mode") != "workplace"
    ):
        return redirect(url_for("career"))

    evaluation = attempt.get("evaluation")

    if not isinstance(evaluation, dict):
        return redirect(
            url_for(
                "workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    try:
        score = float(
            evaluation.get("overall_score", 0)
        )
    except (TypeError, ValueError):
        score = 0

    # Interview requires at least 85%.
    if score < 85:
        return redirect(
            url_for(
                "workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    career_id = attempt.get("career_id", "")
    position_id = attempt.get("position_id", "")
    company_id = attempt.get("company_id", "")

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )   

    if not position:
        return redirect(url_for("career"))

    position_title = position.get(
        "title",
        position_id.replace("-", " ").title(),
    )

    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )

    career_title = (
        career_id
        .replace("-", " ")
        .title()
    )

    try:
        if is_backend_demo(career_id, position_id, company_id):
            generated = get_backend_demo_interview()
        else:
            generated = generate_interview_questions(
                workplace_attempt=attempt,
                career_title=career_title,
                position_title=position_title,
                company_name=company_name,
            )

        interview_id = create_interview_attempt(
            user_id=user_id,
            source_attempt_id=attempt_id,
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            interview_data=generated,
        )

    except InterviewGenerationError as error:
        app.logger.exception(
            "Interview generation failed: %s",
            error,
        )

        return redirect(
            url_for(
                "workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    except Exception:
        app.logger.exception(
            "Could not create interview."
        )

        return redirect(
            url_for(
                "workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    return redirect(
        url_for(
            "interview_workspace",
            interview_id=interview_id,
        )
    )

@app.get("/interview/<interview_id>")
def interview_workspace(interview_id):
    """
    Display the active AI job interview.
    """

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return redirect(
            url_for("career")
        )

    # If the interview is already complete,
    # send the user directly to the results.
    if interview.get("status") == "completed":
        return redirect(
            url_for(
                "interview_review",
                interview_id=interview_id,
            )
        )

    if interview.get("status") != "in_progress":
        return redirect(
            url_for("career")
        )

    questions = interview.get(
        "public_questions",
        [],
    )

    if not isinstance(questions, list) or not questions:
        return redirect(
            url_for("career")
        )

    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )

    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )


    # --------------------------------------------------------
    # RECOVER A FINISHED INTERVIEW
    # --------------------------------------------------------
    #
    # Firebase may already contain all 7 answers even when
    # final report generation previously failed.
    #
    # In that case current_question becomes 8. Instead of
    # trapping the candidate, automatically finish the report.

    try:
        current_question = int(
            interview.get(
                "current_question",
                1,
            )
        )
    except (TypeError, ValueError):
        current_question = 1

    if current_question > len(questions):

        raw_answers = interview.get(
            "answers",
            {},
        )

        if isinstance(raw_answers, list):

            answers = {
                str(index): item
                for index, item in enumerate(
                    raw_answers
                )
                if (
                    index > 0
                    and isinstance(
                        item,
                        dict,
                    )
                )
            }

        elif isinstance(raw_answers, dict):

            answers = {
                str(key): value
                for key, value in raw_answers.items()
                if isinstance(
                    value,
                    dict,
                )
            }

        else:
            answers = {}

        if len(answers) >= len(questions):

            try:

                final_evaluation = (
                    generate_final_interview_evaluation(
                        answers=answers,
                        questions=questions,
                        company_name=company_name,
                        position_title=position_title,
                    )
                )

                overall_score = (
                    final_evaluation.get(
                        "overall_score",
                        0,
                    )
                )

                complete_interview_attempt(
                    user_id=user_id,
                    interview_id=interview_id,
                    overall_score=overall_score,
                    evaluation=final_evaluation,
                )

                return redirect(
                    url_for(
                        "interview_review",
                        interview_id=interview_id,
                    )
                )

            except InterviewEvaluationError as error:

                app.logger.warning(
                    "Interview recovery evaluation failed: %s",
                    error,
                )


    return render_template(
        "interview.html",

        interview_id=interview_id,

        interview_title=interview.get(
            "interview_title",
            f"{position_title} Interview",
        ),

        opening_message=interview.get(
            "opening_message",
            "Welcome to your CareerGrid interview.",
        ),

        questions=questions,

        career_id=career_id,
        position_id=position_id,
        company_id=company_id,

        position_title=position_title,
        company_name=company_name,

        user_name=session.get(
            "user_name",
            "User",
        ),
    )


@app.post("/api/interview/<interview_id>/answer")
def submit_interview_answer(interview_id):

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return jsonify(
            {
                "error":
                "Interview attempt not found."
            }
        ), 404


    if interview.get("status") != "in_progress":
        return jsonify(
            {
                "error":
                "This interview is already completed."
            }
        ), 400


    try:
        question_id = int(
            request.form.get(
                "question_id",
                "0",
            )
        )

    except ValueError:
        return jsonify(
            {
                "error":
                "Invalid question ID."
            }
        ), 400


    try:
        duration_seconds = float(
            request.form.get(
                "duration_seconds",
                "0",
            )
        )

    except ValueError:
        duration_seconds = 0


    try:
        speaking_seconds = float(
            request.form.get(
                "speaking_seconds",
                "0",
            )
        )
    except (TypeError, ValueError):
        speaking_seconds = 0

    try:
        silence_seconds = float(
            request.form.get(
                "silence_seconds",
                "0",
            )
        )
    except (TypeError, ValueError):
        silence_seconds = 0

    try:
        silence_ratio = float(
            request.form.get(
                "silence_ratio",
                "0",
            )
        )
    except (TypeError, ValueError):
        silence_ratio = 0

    try:
        measured_long_pause_count = int(
            request.form.get(
                "long_pause_count",
                "0",
            )
        )
    except (TypeError, ValueError):
        measured_long_pause_count = 0

    try:
        longest_pause_seconds = float(
            request.form.get(
                "longest_pause_seconds",
                "0",
            )
        )
    except (TypeError, ValueError):
        longest_pause_seconds = 0
    audio_file = request.files.get(
        "audio"
    )


    if not audio_file:
        return jsonify(
            {
                "error":
                "No microphone recording was received."
            }
        ), 400


    audio_bytes = audio_file.read()


    if not audio_bytes:
        return jsonify(
            {
                "error":
                "The microphone recording was empty."
            }
        ), 400


    # Keep uploads reasonably bounded.
    if len(audio_bytes) > 15 * 1024 * 1024:
        return jsonify(
            {
                "error":
                "The recording is too large."
            }
        ), 413


    questions = interview.get(
        "public_questions",
        [],
    )


    question = next(
        (
            item
            for item in questions
            if int(
                item.get(
                    "id",
                    0,
                )
            ) == question_id
        ),
        None,
    )


    if not question:
        return jsonify(
            {
                "error":
                "Interview question not found."
            }
        ), 404


    expected_question = int(
        interview.get(
            "current_question",
            1,
        )
    )


    if question_id != expected_question:
        return jsonify(
            {
                "error":
                "Please answer the current interview question."
            }
        ), 409


    rubrics = interview.get(
        "private_rubrics",
        {},
    )

    # Firebase Realtime Database may deserialize
    # sequential numeric keys as a list instead of a dict.
    if isinstance(rubrics, list):

        rubric = (
            rubrics[question_id]
            if (
                0 <= question_id < len(rubrics)
                and isinstance(
                    rubrics[question_id],
                    dict,
                )
            )
            else {}
        )

    elif isinstance(rubrics, dict):

        rubric = rubrics.get(
            str(question_id),
            rubrics.get(
                question_id,
                {},
            ),
        )

    else:
        rubric = {}

    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )


    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )


    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )


    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )


    mime_type = (
        audio_file.mimetype
        or "audio/webm"
    )


    try:

        analysis = analyze_spoken_answer(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            question=question,
            rubric=rubric,
            duration_seconds=duration_seconds,
            company_name=company_name,
            position_title=position_title,
        )

        analysis["speech_measurements"] = {
            "duration_seconds": round(
                max(
                    duration_seconds,
                    0,
                ),
                2,
            ),

            "speaking_seconds": round(
                max(
                    speaking_seconds,
                    0,
                ),
                2,
            ),

            "silence_seconds": round(
                max(
                    silence_seconds,
                    0,
                ),
                2,
            ),

            "silence_ratio": round(
                max(
                    0,
                    min(
                        silence_ratio,
                        1,
                    ),
                ),
                4,
            ),

            "long_pause_count":
                max(
                    measured_long_pause_count,
                    0,
                ),

            "longest_pause_seconds":
                round(
                    max(
                        longest_pause_seconds,
                        0,
                    ),
                    2,
                ),
        }

        # Prefer actual browser-measured pauses over
        # the model's estimate from the recording.
        analysis["long_pause_count"] = max(
            measured_long_pause_count,
            0,
        )


        save_interview_answer(
            user_id=user_id,
            interview_id=interview_id,
            question_id=question_id,
            answer_data=analysis,
        )


    except InterviewEvaluationError as error:

        app.logger.warning(
            "Interview answer evaluation failed: %s",
            error,
        )

        return jsonify(
            {
                "error":
                "CareerGrid could not evaluate your recording. Please try again."
            }
        ), 503


    except Exception as error:

        app.logger.exception(
            "Could not save interview answer."
        )

        return jsonify(
            {
                "error": (
                    "Could not save your interview answer: "
                    f"{type(error).__name__}: {error}"
                )
            }
        ), 500


    # -----------------------------------------------------
    # If there are more questions, continue.
    # -----------------------------------------------------

    if question_id < len(questions):

        return jsonify(
            {
                "saved": True,
                "completed": False,
                "question_score":
                    analysis.get(
                        "question_score"
                    ),
            }
        )


    # -----------------------------------------------------
    # Final question completed.
    # Generate overall report.
    # -----------------------------------------------------

    refreshed = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )


    answers = (
        refreshed.get(
            "answers",
            {},
        )
        if refreshed
        else {}
    )


    try:

        final_evaluation = (
            generate_final_interview_evaluation(
                answers=answers,
                questions=questions,
                company_name=company_name,
                position_title=position_title,
            )
        )


        overall_score = (
            final_evaluation.get(
                "overall_score",
                0,
            )
        )


        complete_interview_attempt(
            user_id=user_id,
            interview_id=interview_id,
            overall_score=overall_score,
            evaluation=final_evaluation,
        )


    except InterviewEvaluationError as error:

        app.logger.warning(
            "Final interview evaluation failed: %s",
            error,
        )

        return jsonify(
            {
                "error":
                "Your answers were saved, but CareerGrid could not create the final report."
            }
        ), 503


    return jsonify(
        {
            "saved": True,
            "completed": True,

            "review_url": url_for(
                "interview_review",
                interview_id=interview_id,
            ),
        }
    )

@app.get("/interview/<interview_id>/review")
def interview_review(interview_id):

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return redirect(
            url_for("career")
        )


    if interview.get("status") != "completed":

        return redirect(
            url_for(
                "interview_workspace",
                interview_id=interview_id,
            )
        )


    evaluation = interview.get(
        "evaluation",
        {},
    )


    questions = interview.get(
        "public_questions",
        [],
    )


    raw_answers = interview.get(
        "answers",
        {},
    )

    if isinstance(raw_answers, list):

        answers = {
            str(index): item
            for index, item in enumerate(
                raw_answers
            )
            if (
                index > 0
                and isinstance(
                    item,
                    dict,
                )
            )
        }

    elif isinstance(raw_answers, dict):

        answers = {
            str(key): value
            for key, value in raw_answers.items()
            if isinstance(
                value,
                dict,
            )
        }

    else:
        answers = {}


    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )


    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )


    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )


    company_name = _company_display_name(
        career_id,
        position_id,
        company_id,
    )


    question_results = []

    for question in questions:

        question_id = str(
            question.get("id")
        )

        answer = answers.get(
            question_id,
            {},
        )

        question_results.append(
            {
                "question":
                    question.get(
                        "question"
                    ),

                "category":
                    question.get(
                        "category"
                    ),

                "score":
                    answer.get(
                        "question_score",
                        0,
                    ),

                "transcript":
                    answer.get(
                        "transcript",
                        "",
                    ),

                "feedback":
                    answer.get(
                        "feedback",
                        "",
                    ),

                "word_count":
                    answer.get(
                        "word_count",
                        0,
                    ),

                "words_per_minute":
                    answer.get(
                        "words_per_minute",
                        0,
                    ),

                "filler_count":
                    answer.get(
                        "filler_count",
                        0,
                    ),

                "filler_rate_percent":
                    answer.get(
                        "filler_rate_percent",
                        0,
                    ),

                "long_pause_count":
                    answer.get(
                        "long_pause_count",
                        0,
                    ),
            }
        )


    return render_template(
        "interview_review.html",

        interview_id=interview_id,

        evaluation=evaluation,

        overall_score=evaluation.get(
            "overall_score",
            0,
        ),

        company_name=company_name,

        position_title=position_title,

        question_results=question_results,

        strengths=evaluation.get(
            "strengths",
            [],
        ),

        areas_for_improvement=evaluation.get(
            "areas_for_improvement",
            [],
        ),

        next_steps=evaluation.get(
            "next_steps",
            [],
        ),
    )

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

    return _company_display_name(career_id, position_id, company_id)


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
