"""External job-listing integrations used by CareerGrid selection pages.

Every search returns an explicit status so the UI can tell apart: live results,
no matching jobs, a provider that is not configured, a provider error, and a
location no configured provider supports. Listings are never fabricated, and
provider keys stay on the server.
"""

import logging
import re
from typing import Any

import requests

from constants import (
    ADZUNA_SEARCH_URL_TEMPLATE,
    ADZUNA_SUPPORTED_COUNTRIES,
    JOB_SEARCH_DEFAULT_COUNTRY,
    JOB_SEARCH_EXTRA_COUNTRIES,
    JOOBLE_SEARCH_URL_TEMPLATE,
    LEBANON_LOCATION_TERMS,
)

logger = logging.getLogger(__name__)

STATUS_OK = "ok"
STATUS_NO_RESULTS = "no_results"
STATUS_NOT_CONFIGURED = "not_configured"
STATUS_PROVIDER_ERROR = "provider_error"
STATUS_UNSUPPORTED_LOCATION = "unsupported_location"

PROVIDER_LABELS = {"adzuna": "Adzuna", "jooble": "Jooble"}
ATTRIBUTION = {
    "adzuna": {"label": "Jobs by Adzuna", "url": "https://www.adzuna.com"},
    "jooble": {"label": "Jobs by Jooble", "url": "https://jooble.org"},
}


def supported_countries() -> list[dict[str, str]]:
    """Return every selectable country with the provider that would serve it."""

    countries = [
        {"code": code, "name": name, "provider": "adzuna"}
        for code, name in ADZUNA_SUPPORTED_COUNTRIES.items()
    ]
    countries += [
        {"code": code, "name": name, "provider": "jooble"}
        for code, name in JOB_SEARCH_EXTRA_COUNTRIES.items()
    ]
    return sorted(countries, key=lambda item: item["name"])


def normalize_country(value: str | None, default: str = JOB_SEARCH_DEFAULT_COUNTRY) -> str:
    code = str(value or default or "").strip().lower()
    return code if re.fullmatch(r"[a-z]{2}", code) else ""


def country_name(code: str) -> str:
    return ADZUNA_SUPPORTED_COUNTRIES.get(code) or JOB_SEARCH_EXTRA_COUNTRIES.get(code) or code.upper()


def _clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _safe_url(value: Any) -> str:
    url = str(value or "").strip()
    return url if url.startswith("https://") or url.startswith("http://") else ""


def _result(status: str, *, provider: str | None, country: str, location: str, jobs=None, message: str = "") -> dict[str, Any]:
    return {
        "status": status,
        "provider": provider,
        "provider_label": PROVIDER_LABELS.get(provider or "", ""),
        "attribution": ATTRIBUTION.get(provider or ""),
        "country": country,
        "country_name": country_name(country) if country else "",
        "location": location,
        "jobs": jobs or [],
        "message": message,
    }


def _normalize_adzuna_job(job: dict[str, Any], fallback_title: str) -> dict[str, Any]:
    company = job.get("company") or {}
    location = job.get("location") or {}
    return {
        "title": _clean_text(job.get("title"), 200) or fallback_title,
        "company_name": _clean_text(company.get("display_name"), 200),
        "location": _clean_text(location.get("display_name"), 200),
        "description": _clean_text(job.get("description"), 1500),
        "url": _safe_url(job.get("redirect_url")),
        "created": _clean_text(job.get("created"), 40),
        "source": "adzuna",
        "source_label": "Adzuna",
    }


def _search_adzuna(job_title, *, country, location, results, app_id, app_key, timeout_seconds):
    if not app_id or not app_key:
        return _result(
            STATUS_NOT_CONFIGURED, provider="adzuna", country=country, location=location,
            message="Live job listings are not configured on this server (ADZUNA_APP_ID / ADZUNA_APP_KEY).",
        )
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": job_title,
        "results_per_page": results,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location
    try:
        response = requests.get(
            ADZUNA_SEARCH_URL_TEMPLATE.format(country=country),
            params=params,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        # Never log the request URL: it carries the provider key.
        logger.warning("Adzuna job lookup failed: %s", type(error).__name__)
        return _result(
            STATUS_PROVIDER_ERROR, provider="adzuna", country=country, location=location,
            message="The job provider could not be reached. Try again later or use a practice option below.",
        )
    jobs = [
        _normalize_adzuna_job(job, job_title)
        for job in (data.get("results") or [])
        if isinstance(job, dict)
    ]
    jobs = [job for job in jobs if job["company_name"]]
    if not jobs:
        return _result(
            STATUS_NO_RESULTS, provider="adzuna", country=country, location=location,
            message=f"No live {job_title} listings matched in {country_name(country)} right now.",
        )
    return _result(STATUS_OK, provider="adzuna", country=country, location=location, jobs=jobs)


def _in_lebanon(location: str) -> bool:
    lower = location.lower()
    return any(term in lower for term in LEBANON_LOCATION_TERMS)


def _search_jooble_lebanon(job_title, *, country, location, results, api_key, timeout_seconds):
    if not api_key:
        return _result(
            STATUS_UNSUPPORTED_LOCATION, provider=None, country=country, location=location,
            message=(
                "Live listings for Lebanon are not available. Adzuna does not cover Lebanon, "
                "and no provider with Lebanese coverage is configured on this server. "
                "You can still practise with a demo company or paste a job description."
            ),
        )
    try:
        response = requests.post(
            JOOBLE_SEARCH_URL_TEMPLATE.format(api_key=api_key),
            json={"keywords": job_title, "location": location or "Lebanon"},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        logger.warning("Jooble job lookup failed: %s", type(error).__name__)
        return _result(
            STATUS_PROVIDER_ERROR, provider="jooble", country=country, location=location,
            message="The job provider could not be reached. Try again later or use a practice option below.",
        )
    jobs = []
    for job in data.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        job_location = _clean_text(job.get("location"), 200)
        # Keep only listings the provider itself places in Lebanon.
        if not _in_lebanon(job_location):
            continue
        jobs.append(
            {
                "title": _clean_text(job.get("title"), 200) or job_title,
                "company_name": _clean_text(job.get("company"), 200),
                "location": job_location,
                "description": _clean_text(job.get("snippet"), 1500),
                "url": _safe_url(job.get("link")),
                "created": _clean_text(job.get("updated"), 40),
                "source": "jooble",
                "source_label": "Jooble",
            }
        )
    jobs = [job for job in jobs if job["company_name"]][:results]
    if not jobs:
        return _result(
            STATUS_NO_RESULTS, provider="jooble", country=country, location=location,
            message=f"No live {job_title} listings located in Lebanon were returned right now.",
        )
    return _result(STATUS_OK, provider="jooble", country=country, location=location, jobs=jobs)


def search_jobs(
    job_title: str,
    *,
    country: str | None,
    location: str = "",
    results: int = 5,
    adzuna_app_id: str | None = None,
    adzuna_app_key: str | None = None,
    jooble_api_key: str | None = None,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """Search the provider that genuinely covers ``country``."""

    code = normalize_country(country)
    location = _clean_text(location, 100)
    if code in ADZUNA_SUPPORTED_COUNTRIES:
        return _search_adzuna(
            job_title, country=code, location=location, results=results,
            app_id=adzuna_app_id, app_key=adzuna_app_key, timeout_seconds=timeout_seconds,
        )
    if code == "lb":
        return _search_jooble_lebanon(
            job_title, country=code, location=location, results=results,
            api_key=jooble_api_key, timeout_seconds=timeout_seconds,
        )
    return _result(
        STATUS_UNSUPPORTED_LOCATION, provider=None, country=code, location=location,
        message=f"Live listings are not available for {country_name(code) if code else 'that location'}.",
    )
