"""Career browsing, position selection, and company routes."""

import re

from flask import Blueprint, current_app, jsonify, redirect, session, url_for

from routes.frontend import serve_react_app

from services.simulation.backend_demo_scenario_service import (
    BACKEND_DEMO_CAREER_ID,
    BACKEND_DEMO_POSITION_ID,
    get_backend_demo_job,
)
from services.simulation.career_service import (
    POSITIONS_DATA,
    get_career_display_name,
    get_career_cards,
    is_position_available,
)
from services.simulation.job_service import fetch_adzuna_jobs

careers_bp = Blueprint("careers", __name__)


def _company_cards(career_id, position_id):
    """Return the browser-safe company choices used by the selection UI."""

    position = POSITIONS_DATA.get(career_id, {}).get(position_id)
    if not position or not is_position_available(career_id, position_id):
        return None

    jobs = fetch_adzuna_jobs(
        position["title"],
        results=current_app.config["ADZUNA_DEFAULT_RESULTS"],
        app_id=current_app.config.get("ADZUNA_APP_ID"),
        app_key=current_app.config.get("ADZUNA_APP_KEY"),
        timeout_seconds=current_app.config["ADZUNA_REQUEST_TIMEOUT_SECONDS"],
    )
    cards = []
    if career_id == BACKEND_DEMO_CAREER_ID and position_id == BACKEND_DEMO_POSITION_ID:
        cards.append({**get_backend_demo_job(), "status": "Demo"})
    if jobs:
        for job in jobs:
            company = job.get("company", {})
            location = job.get("location", {})
            description = re.sub(r"<[^>]+>", "", str(job.get("description", ""))).strip()
            cards.append(
                {
                    "title": job.get("title") or position["title"],
                    "company_id": company.get("display_name", ""),
                    "company_name": company.get("display_name", ""),
                    "location": location.get("display_name", ""),
                    "description": description[:230],
                    "job_source": "adzuna",
                    "status": "Open",
                }
            )
    else:
        for company in position.get("companies", []):
            cards.append(
                {
                    "title": position["title"],
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "location": company["location"],
                    "description": "Practice a simulated task for this role while live listings are unavailable.",
                    "job_source": "demo",
                    "status": "Demo",
                }
            )
    return cards


@careers_bp.get("/api/careers")
def career_catalog_api():
    """Expose the public career-card metadata owned by the service layer."""

    return jsonify({"careers": get_career_cards()})


@careers_bp.get("/api/careers/<career_id>/positions")
def position_catalog_api(career_id):
    """Expose display-only position choices for one career."""

    positions = POSITIONS_DATA.get(career_id)
    if positions is None:
        return jsonify({"error": "Career not found."}), 404
    return jsonify(
        {
            "career_id": career_id,
            "career_name": get_career_display_name(career_id),
            "positions": [
                {"id": position_id, "title": position["title"], "available": position.get("available", False)}
                for position_id, position in positions.items()
            ],
        }
    )


@careers_bp.get("/api/careers/<career_id>/positions/<position_id>/companies")
def company_catalog_api(career_id, position_id):
    """Return server-resolved Adzuna, demo, or fallback company cards."""

    companies = _company_cards(career_id, position_id)
    if companies is None:
        return jsonify({"error": "Position not found or unavailable."}), 404
    position = POSITIONS_DATA[career_id][position_id]
    return jsonify(
        {
            "career_id": career_id,
            "career_name": get_career_display_name(career_id),
            "position_id": position_id,
            "position_title": position["title"],
            "companies": companies,
        }
    )

# =========================================================
# MAIN WEBSITE ROUTES
# =========================================================

@careers_bp.route("/")
def home():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    return serve_react_app()


@careers_bp.route("/career")
def career():
    return serve_react_app()


@careers_bp.route("/positions/<career_id>")
def positions(career_id):
    return serve_react_app()


@careers_bp.route("/positions/<career_id>/<position_id>")
def companies(career_id, position_id):
    position_data = POSITIONS_DATA.get(career_id, {}).get(position_id, {})
    if not position_data or not is_position_available(career_id, position_id):
        return redirect(url_for("careers.positions", career_id=career_id))

    return serve_react_app()
