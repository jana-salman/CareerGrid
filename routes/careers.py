"""Career browsing, position selection, and company routes."""

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

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
from services.simulation.job_service import search_jobs, supported_countries

careers_bp = Blueprint("careers", __name__)


def _job_search(position, country):
    """Search the provider that genuinely covers the selected country."""

    return search_jobs(
        position["title"],
        country=country or current_app.config.get("JOB_SEARCH_COUNTRY"),
        location=current_app.config.get("JOB_SEARCH_LOCATION", ""),
        results=current_app.config["ADZUNA_DEFAULT_RESULTS"],
        adzuna_app_id=current_app.config.get("ADZUNA_APP_ID"),
        adzuna_app_key=current_app.config.get("ADZUNA_APP_KEY"),
        jooble_api_key=current_app.config.get("JOOBLE_API_KEY"),
        timeout_seconds=current_app.config["ADZUNA_REQUEST_TIMEOUT_SECONDS"],
    )


def _company_cards(career_id, position_id, country=None):
    """Return browser-safe company choices plus the live-search status."""

    position = POSITIONS_DATA.get(career_id, {}).get(position_id)
    if not position or not is_position_available(career_id, position_id):
        return None, None

    search = _job_search(position, country)
    cards = []
    if career_id == BACKEND_DEMO_CAREER_ID and position_id == BACKEND_DEMO_POSITION_ID:
        cards.append(
            {
                **get_backend_demo_job(),
                "status": "Demo",
                "listing_kind": "practice",
                "source_label": "CareerGrid practice scenario",
            }
        )
    for job in search["jobs"]:
        cards.append(
            {
                "title": job["title"],
                "company_id": job["company_name"],
                "company_name": job["company_name"],
                "location": job["location"],
                "description": job["description"][:230],
                "full_description": job["description"],
                "job_source": job["source"],
                "source_label": job["source_label"],
                "url": job["url"],
                "created": job["created"],
                "status": "Live listing",
                "listing_kind": "live",
            }
        )
    if not search["jobs"]:
        for company in position.get("companies", []):
            cards.append(
                {
                    "title": position["title"],
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "location": company["location"],
                    "description": (
                        "Practice a simulated task for this role. This fictional "
                        "company is not a live vacancy."
                    ),
                    "job_source": "demo",
                    "source_label": "CareerGrid practice scenario",
                    "status": "Demo",
                    "listing_kind": "practice",
                }
            )
    job_search = {key: value for key, value in search.items() if key != "jobs"}
    job_search["supported_countries"] = supported_countries()
    return cards, job_search


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

    companies, job_search = _company_cards(
        career_id, position_id, request.args.get("country")
    )
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
            "job_search": job_search,
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
