"""Career browsing, position selection, and company routes."""

from flask import Blueprint, current_app, redirect, render_template, session, url_for

from services.backend_demo_scenario_service import (
    BACKEND_DEMO_CAREER_ID,
    BACKEND_DEMO_POSITION_ID,
    get_backend_demo_job,
)
from services.career_service import (
    POSITIONS_DATA,
    get_career_display_name,
    get_career_cards,
    is_position_available,
)
from services.job_service import fetch_adzuna_jobs

careers_bp = Blueprint("careers", __name__)

# =========================================================
# MAIN WEBSITE ROUTES
# =========================================================

@careers_bp.route("/")
def home():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "home.html",
        user_name=session.get("user_name"),
    )


@careers_bp.route("/career")
def career():
    return render_template(
        "career.html",
        careers=get_career_cards(),
        user_name=session.get("user_name"),
    )


@careers_bp.route("/positions/<career_id>")
def positions(career_id):
    career_name = get_career_display_name(career_id)

    position_data = POSITIONS_DATA.get(career_id, {})

    return render_template(
        "positions.html",
        career_id=career_id,
        career_name=career_name,
        positions=position_data,
    )


@careers_bp.route("/positions/<career_id>/<position_id>")
def companies(career_id, position_id):
    career_name = get_career_display_name(career_id)

    position_data = POSITIONS_DATA.get(career_id, {}).get(position_id, {})
    if not position_data or not is_position_available(career_id, position_id):
        return redirect(url_for("careers.positions", career_id=career_id))

    position_title = position_data.get("title", "")
    local_companies = position_data.get("companies", [])

    jobs = fetch_adzuna_jobs(
        position_title,
        results=current_app.config["ADZUNA_DEFAULT_RESULTS"],
        app_id=current_app.config.get("ADZUNA_APP_ID"),
        app_key=current_app.config.get("ADZUNA_APP_KEY"),
        timeout_seconds=current_app.config["ADZUNA_REQUEST_TIMEOUT_SECONDS"],
    )

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
