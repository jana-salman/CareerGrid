"""Sanitize the live job listing a participant selected.

Job text is external, untrusted data. It is only ever passed to the task
generator as delimited reference data, never as instructions.
"""

import re
from typing import Any

LIVE_SOURCES = {"adzuna": "Adzuna listing", "jooble": "Jooble listing"}
CATALOG_SOURCE = "catalog"
MAX_JOB_DESCRIPTION_LENGTH = 4000
# Provider APIs often return only the first few hundred characters of a
# listing. Anything this short, or visibly truncated, is marked as an excerpt so
# the generator does not invent the missing employer requirements.
EXCERPT_LENGTH = 700

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


class JobContextError(ValueError):
    """Raised when supplied job details cannot be used."""


def _clean(value: Any, limit: int) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = _CONTROL.sub(" ", text)
    # Contact details are not needed to design a task.
    text = _EMAIL.sub("[email removed]", text)
    text = _PHONE.sub("[phone removed]", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def build_job_context(job_source: str, raw: Any) -> dict[str, Any] | None:
    """Return a sanitized job context, or None when none was supplied."""

    if not isinstance(raw, dict) or job_source not in LIVE_SOURCES:
        return None
    context = {
        "title": _clean(raw.get("title"), 160),
        "company": _clean(raw.get("company"), 160),
        "location": _clean(raw.get("location"), 160),
        "description": _clean(raw.get("description"), MAX_JOB_DESCRIPTION_LENGTH),
    }
    url = str(raw.get("url") or "").strip()
    description = context["description"]
    context.update(
        source=job_source,
        source_label=LIVE_SOURCES[job_source],
        url=url if url.startswith(("https://", "http://")) else "",
        excerpt=len(description) < EXCERPT_LENGTH or description.endswith(("…", "...")),
    )
    return context if context["title"] or context["description"] else None


def build_catalog_job_context(position_id: str, company_id: str) -> dict[str, Any] | None:
    """Role context for a CareerGrid practice company (not a real listing)."""

    from services.simulation.career_service import get_company_role_context

    profile = get_company_role_context(position_id, company_id)
    if not profile:
        return None
    return {
        **profile,
        "location": "",
        "source": CATALOG_SOURCE,
        "source_label": "CareerGrid practice company profile",
        "url": "",
        "excerpt": False,
    }


def simulation_notice(job_context: dict[str, Any] | None, *, fallback: bool = False) -> str:
    """User-facing notice separating the simulation from any real employer."""

    if fallback:
        base = "Practice simulation using CareerGrid's built-in assignment."
    elif job_context and job_context.get("source") == CATALOG_SOURCE:
        base = f"Practice simulation for {job_context.get('company') or 'a CareerGrid practice company'}."
    elif job_context and job_context.get("source") in LIVE_SOURCES:
        company = job_context.get("company") or "the employer"
        base = (
            f"Practice simulation inspired by the {job_context.get('title') or 'selected'} listing "
            f"at {company} ({job_context['source_label']}). {company} did not create or review this task."
        )
    else:
        base = "Practice simulation."
    return f"{base} The company, people, code, and messages are fictional. This is not a real employer assignment."
