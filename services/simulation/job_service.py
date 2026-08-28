"""External job-listing integration used by CareerGrid selection pages."""

import logging
from typing import Any

import requests

from constants import ADZUNA_SEARCH_URL

logger = logging.getLogger(__name__)


def fetch_adzuna_jobs(
    job_title: str,
    location: str = "",
    results: int = 5,
    *,
    app_id: str | None,
    app_key: str | None,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    """Return Adzuna listings, or an empty list when the service is unavailable."""

    if not app_id or not app_key:
        return []

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": job_title,
        "where": location,
        "results_per_page": results,
        "content-type": "application/json",
    }

    try:
        response = requests.get(
            ADZUNA_SEARCH_URL,
            params=params,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as error:
        logger.warning("Adzuna job lookup failed: %s", error)
        return []

    return data.get("results", [])
