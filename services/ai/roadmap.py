"""The personalised learning roadmap: one validated schema end to end.

Every roadmap item has exactly this shape, on save and on load::

    {
        "skill": str,
        "evidence": str,
        "gap": str,
        "next_steps": [str, ...],          # readable sentences, never objects
        "resources": [                     # 0-2 entries from the curated catalog
            {"id", "title", "provider", "url", "relevance"}
        ],
    }

The evaluator chooses resource IDs from ``RESOURCE_CATALOG``; it never writes
URLs. IDs are resolved here, so a report can only link to catalog entries,
and only through safe http(s) URLs.

Older reports stored Python dictionaries as text (for example
``"{'skill': 'Testing', 'next_steps': [...]}"`` inside ``next_steps``). Those
are recovered by parsing literals only (``json.loads`` or
``ast.literal_eval``, which never runs code); anything unparseable is dropped
instead of being shown or guessed.
"""

from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from typing import Any
from urllib.parse import urlsplit

MAX_ITEMS = 5
MAX_STEPS = 4
MAX_RESOURCES = 2
MAX_LITERAL_LENGTH = 8000

# Free, official or open learning material. Every URL was checked to load
# (HTTP 200) on 2026-11-16. "skills" are the tags used for matching.
RESOURCE_CATALOG: dict[str, dict[str, Any]] = {
    "python-errors": {
        "title": "Errors and Exceptions (Python tutorial)", "provider": "Python documentation",
        "url": "https://docs.python.org/3/tutorial/errors.html",
        "skills": ["python", "error handling", "exceptions", "validation", "edge cases", "technical accuracy"],
        "summary": "Explains raising and handling exceptions so invalid input fails clearly.",
    },
    "python-logging": {
        "title": "Logging HOWTO", "provider": "Python documentation",
        "url": "https://docs.python.org/3/howto/logging.html",
        "skills": ["logs", "logging", "investigation", "debugging", "problem solving", "root cause"],
        "summary": "Shows how application logs are produced, which helps you read and trace them.",
    },
    "python-pdb": {
        "title": "pdb: the Python debugger", "provider": "Python documentation",
        "url": "https://docs.python.org/3/library/pdb.html",
        "skills": ["debugging", "python", "investigation", "problem solving", "root cause", "tracing"],
        "summary": "Step through code to confirm how data flows before changing it.",
    },
    "python-mock": {
        "title": "unittest.mock", "provider": "Python documentation",
        "url": "https://docs.python.org/3/library/unittest.mock.html",
        "skills": ["testing", "mocking", "unit tests", "verification", "python"],
        "summary": "Isolate the code under test from storage and external services.",
    },
    "pytest-start": {
        "title": "Get started with pytest", "provider": "pytest documentation",
        "url": "https://docs.pytest.org/en/stable/getting-started.html",
        "skills": ["testing", "pytest", "regression tests", "verification", "verification testing", "python"],
        "summary": "Covers writing and running focused tests for the behaviour you change.",
    },
    "pytest-parametrize": {
        "title": "How to parametrize fixtures and test functions", "provider": "pytest documentation",
        "url": "https://docs.pytest.org/en/stable/how-to/parametrize.html",
        "skills": ["edge cases", "testing", "boundary", "invalid input", "regression tests", "verification testing"],
        "summary": "Test many edge-case inputs (empty, negative, duplicate) with one test.",
    },
    "flask-testing": {
        "title": "Testing Flask Applications", "provider": "Flask documentation",
        "url": "https://flask.palletsprojects.com/en/stable/testing/",
        "skills": ["flask", "api testing", "testing", "endpoints", "verification", "regression tests"],
        "summary": "Test endpoints with the Flask test client, including error responses.",
    },
    "flask-errors": {
        "title": "Handling Application Errors", "provider": "Flask documentation",
        "url": "https://flask.palletsprojects.com/en/stable/errorhandling/",
        "skills": ["flask", "error handling", "api", "status codes", "technical accuracy"],
        "summary": "Return consistent error responses from a Flask API.",
    },
    "mdn-http-status": {
        "title": "HTTP response status codes", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status",
        "skills": ["http", "status codes", "api", "rest", "error handling", "technical accuracy"],
        "summary": "Reference for choosing the right status code (400, 403, 404, 409...).",
    },
    "mdn-idempotent": {
        "title": "Idempotent (glossary)", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Glossary/Idempotent",
        "skills": ["idempotency", "duplicates", "retries", "api", "http"],
        "summary": "Explains why repeated requests must not apply a change twice.",
    },
    "api-design": {
        "title": "Web API design best practices", "provider": "Microsoft Learn",
        "url": "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design",
        "skills": ["api", "rest", "api design", "backward compatibility", "contracts", "pagination"],
        "summary": "Design request/response contracts that stay consistent and compatible.",
    },
    "owasp-input-validation": {
        "title": "Input Validation Cheat Sheet", "provider": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html",
        "skills": ["validation", "input validation", "edge cases", "security", "invalid input"],
        "summary": "Practical rules for validating input at the boundary of a service.",
    },
    "owasp-authorization": {
        "title": "Authorization Cheat Sheet", "provider": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
        "skills": ["authorization", "access control", "security", "ownership", "permissions"],
        "summary": "How to check that a user may access a specific record, on every request.",
    },
    "git-branching": {
        "title": "Basic Branching and Merging (Pro Git)", "provider": "Git (Pro Git book)",
        "url": "https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging",
        "skills": ["git", "branches", "git workflow", "git and pr workflow", "version control"],
        "summary": "Work on a short-lived branch and merge it back cleanly.",
    },
    "git-contributing": {
        "title": "Contributing to a Project (commit guidelines)", "provider": "Git (Pro Git book)",
        "url": "https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project",
        "skills": ["git", "commit messages", "git workflow", "git and pr workflow", "communication"],
        "summary": "Write focused commits with messages that explain what changed and why.",
    },
    "github-pull-requests": {
        "title": "About pull requests", "provider": "GitHub Docs",
        "url": "https://docs.github.com/en/pull-requests/reference/pull-requests",
        "skills": ["pull requests", "code review", "git workflow", "git and pr workflow"],
        "summary": "How pull requests let teammates review a change before it reaches main.",
    },
    "missing-semester-git": {
        "title": "Version Control (Git) - The Missing Semester", "provider": "MIT (open course)",
        "url": "https://missing.csail.mit.edu/2020/version-control/",
        "skills": ["git", "version control", "git workflow", "git and pr workflow"],
        "summary": "A free lecture that builds a solid mental model of Git.",
    },
    "missing-semester-debugging": {
        "title": "Debugging and Profiling - The Missing Semester", "provider": "MIT (open course)",
        "url": "https://missing.csail.mit.edu/2020/debugging-profiling/",
        "skills": ["debugging", "logs", "investigation", "problem solving", "root cause", "root cause reasoning"],
        "summary": "A free lecture on systematic debugging with logs and debuggers.",
    },
    "google-tech-writing": {
        "title": "Technical Writing One", "provider": "Google for Developers (free course)",
        "url": "https://developers.google.com/tech-writing/one",
        "skills": ["communication", "writing", "documentation", "handover", "reporting"],
        "summary": "A free course on writing clear, concise technical explanations.",
    },
    "google-code-review": {
        "title": "The Code Review Developer Guide (author's guide)", "provider": "Google Engineering Practices",
        "url": "https://google.github.io/eng-practices/review/developer/",
        "skills": ["code review", "pull requests", "small changes", "communication", "scope", "scope and independence", "independence"],
        "summary": "Keep changes small and well described so they are easy to review.",
    },
    "mdn-accessibility": {
        "title": "Accessibility (Learn web development)", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility",
        "skills": ["accessibility", "a11y", "semantic html", "aria", "frontend"],
        "summary": "Build interfaces that work for keyboard and assistive-technology users.",
    },
    "webaim-keyboard": {
        "title": "Keyboard Accessibility", "provider": "WebAIM",
        "url": "https://webaim.org/techniques/keyboard/",
        "skills": ["keyboard", "focus", "accessibility", "frontend"],
        "summary": "Check focus order, visible focus, and keyboard activation.",
    },
    "w3c-accessibility-intro": {
        "title": "Introduction to Web Accessibility", "provider": "W3C WAI",
        "url": "https://www.w3.org/WAI/fundamentals/accessibility-intro/",
        "skills": ["accessibility", "a11y", "frontend"],
        "summary": "Why accessibility matters and the principles behind it.",
    },
    "mdn-responsive": {
        "title": "Responsive design", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design",
        "skills": ["responsive", "css", "layout", "mobile", "viewport", "investigation", "frontend"],
        "summary": "Make layouts work at small and large screen sizes.",
    },
    "mdn-dom": {
        "title": "Document Object Model (DOM)", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model",
        "skills": ["dom", "javascript", "selectors", "frontend", "implementation quality"],
        "summary": "How scripts find and update page elements safely.",
    },
    "mdn-events": {
        "title": "Introduction to events", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Events",
        "skills": ["events", "javascript", "click handlers", "frontend", "implementation quality"],
        "summary": "Wire interactive controls with event listeners that behave predictably.",
    },
    "mdn-js-debugging": {
        "title": "What went wrong? Troubleshooting JavaScript", "provider": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/What_went_wrong",
        "skills": ["debugging", "javascript", "console errors", "root cause", "root cause reasoning", "frontend"],
        "summary": "Read console errors and trace a broken script back to its cause.",
    },
    "chrome-devtools-debugging": {
        "title": "Debug JavaScript (Chrome DevTools)", "provider": "Chrome for Developers",
        "url": "https://developer.chrome.com/docs/devtools/javascript",
        "skills": ["debugging", "devtools", "javascript", "investigation", "frontend"],
        "summary": "Use breakpoints to watch values change while reproducing a problem.",
    },
    "node-test": {
        "title": "Test runner (node:test)", "provider": "Node.js documentation",
        "url": "https://nodejs.org/api/test.html",
        "skills": ["testing", "javascript", "unit tests", "node", "testing and verification", "regression"],
        "summary": "Write unit tests for JavaScript helpers with Node's built-in runner.",
    },
}

# Evaluation dimensions mapped to the skill tags used for matching.
DIMENSION_SKILLS = {
    "technical_accuracy": "technical accuracy",
    "problem_solving": "problem solving",
    "verification_testing": "verification testing",
    "git_workflow": "git workflow",
    "communication": "communication",
    "independence": "independence",
    "triage_and_prioritization": "communication",
    "investigation": "investigation",
    "root_cause_reasoning": "root cause reasoning",
    "implementation_quality": "implementation quality",
    "testing_and_verification": "testing and verification",
    "accessibility": "accessibility",
    "regression_awareness": "regression",
    "git_and_pr_workflow": "git and pr workflow",
    "scope_and_independence": "scope and independence",
}

STEP_TEXT_KEYS = ("step", "action", "text", "description", "detail", "title", "task", "name", "summary")
SKILL_KEYS = ("skill", "skill_name", "area", "topic")


# ---------------------------------------------------------------------------
# Safe parsing and text extraction
# ---------------------------------------------------------------------------


def safe_url(value: Any) -> str:
    """Return the URL if it is a plain absolute http(s) URL, else ""."""

    url = str(value or "").strip()
    if not url or re.search(r"[\s<>\"'`\\\x00-\x1f]", url):
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
        return ""
    return url


def parse_literal(text: str) -> Any:
    """Parse JSON or a Python literal (dict/list/str/number) without running code.

    ``ast.literal_eval`` only builds literal values; it cannot call functions
    or evaluate expressions. Oversized or invalid input returns None.
    """

    text = str(text or "").strip()
    if not text or len(text) > MAX_LITERAL_LENGTH or text[0] not in "{[":
        return None
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None


def _clean(text: Any, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def _as_roadmap_dict(value: Any) -> dict[str, Any] | None:
    """A roadmap-shaped dict from a dict or from its stored text form."""

    if isinstance(value, str):
        value = parse_literal(value)
    if isinstance(value, dict) and any(_clean(value.get(key), 200) for key in SKILL_KEYS):
        if any(key in value for key in ("evidence", "gap", "next_steps", "steps", "resources", "resource_ids")):
            return value
    return None


def readable_text(value: Any, limit: int = 300) -> str:
    """One readable sentence from a string, a stored literal, or a step object."""

    if isinstance(value, str):
        parsed = parse_literal(value)
        if parsed is None:
            stripped = value.strip()
            # Unparseable or truncated object text is never shown raw.
            return "" if stripped[:1] in "{[" else _clean(stripped, limit)
        value = parsed
    if isinstance(value, dict):
        if _as_roadmap_dict(value) is not None:
            return ""  # a whole roadmap item is not one step
        for key in STEP_TEXT_KEYS:
            text = readable_text(value.get(key), limit) if value.get(key) is not None else ""
            if text:
                return text
        return ""
    if isinstance(value, (list, tuple)):
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _clean(value, limit)
    return ""


def _list(value: Any) -> list[Any]:
    if isinstance(value, str):
        parsed = parse_literal(value)
        if isinstance(parsed, list):
            return parsed
        return [value] if value.strip() else []
    if isinstance(value, dict):
        return [value]
    return list(value) if isinstance(value, (list, tuple)) else []


def _fingerprint(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _stems(text: str) -> set[str]:
    return {word[:-1] if len(word) > 3 and word.endswith("s") else word for word in _fingerprint(text).split()}


def _skill_key(skill: str) -> str:
    words = [word[:-1] if len(word) > 3 and word.endswith("s") else word for word in _fingerprint(skill).split()]
    return " ".join(word for word in words if word not in {"and", "the", "of", "your", "skill", "skills"})


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


def resource_entry(resource_id: str, relevance: str = "") -> dict[str, str] | None:
    entry = RESOURCE_CATALOG.get(str(resource_id or "").strip())
    if not entry or not safe_url(entry["url"]):
        return None
    return {
        "id": str(resource_id).strip(),
        "title": entry["title"],
        "provider": entry["provider"],
        "url": entry["url"],
        "relevance": _clean(relevance, 240) or entry["summary"],
    }


def _catalog_id_for(value: dict[str, Any]) -> str:
    if value.get("id") in RESOURCE_CATALOG:
        return value["id"]
    url = safe_url(value.get("url"))
    return next((key for key, entry in RESOURCE_CATALOG.items() if url and entry["url"] == url), "")


def resolve_resources(selection: Any) -> list[dict[str, str]]:
    """Resolve evaluator-selected IDs (or stored catalog entries) to details.

    Anything not in the catalog, including invented URLs, is discarded.
    """

    resolved: list[dict[str, str]] = []
    for raw in _list(selection):
        if isinstance(raw, str):
            parsed = parse_literal(raw)
            raw = parsed if isinstance(parsed, dict) else {"id": raw}
        if not isinstance(raw, dict):
            continue
        entry = resource_entry(_catalog_id_for(raw), readable_text(raw.get("relevance") or raw.get("why"), 240))
        if entry and entry["id"] not in {item["id"] for item in resolved}:
            resolved.append(entry)
        if len(resolved) == MAX_RESOURCES:
            break
    return resolved


def match_resources(text: str, limit: int = MAX_RESOURCES) -> list[dict[str, str]]:
    """Catalog entries whose skill tags appear in ``text`` (best first)."""

    words = _stems(text)
    scored = []
    for order, (resource_id, entry) in enumerate(RESOURCE_CATALOG.items()):
        # A tag matches when all of its words appear ("edge cases" ~ "edge-case").
        score = sum(len(tag) for tag in entry["skills"] if _stems(tag) <= words)
        if score:
            scored.append((-score, order, resource_id))
    return [entry for _, _, resource_id in sorted(scored)[:limit] if (entry := resource_entry(resource_id))]


def catalog_for_prompt() -> list[dict[str, Any]]:
    return [{"id": key, "title": entry["title"], "skills": entry["skills"]} for key, entry in RESOURCE_CATALOG.items()]


# ---------------------------------------------------------------------------
# Roadmap normalisation
# ---------------------------------------------------------------------------


def _item(raw: dict[str, Any], steps: list[str]) -> dict[str, Any] | None:
    skill = readable_text(next((raw.get(key) for key in SKILL_KEYS if raw.get(key)), ""), 120)
    if not skill:
        return None
    evidence = readable_text(raw.get("evidence"), 600)
    gap = readable_text(raw.get("gap"), 400)
    resources = resolve_resources(raw.get("resources") or raw.get("resource_ids"))
    if not resources:
        resources = match_resources(f"{skill} {gap}")
    return {"skill": skill, "evidence": evidence, "gap": gap, "next_steps": steps[:MAX_STEPS], "resources": resources}


def _merge(into: dict[str, Any], other: dict[str, Any]) -> None:
    for key, limit in (("evidence", 600), ("gap", 400)):
        if other[key] and _fingerprint(other[key]) not in _fingerprint(into[key]):
            into[key] = _clean(f"{into[key]} {other[key]}", limit)
    seen = {_fingerprint(step) for step in into["next_steps"]}
    for step in other["next_steps"]:
        if _fingerprint(step) not in seen and len(into["next_steps"]) < MAX_STEPS:
            into["next_steps"].append(step)
            seen.add(_fingerprint(step))
    for resource in other["resources"]:
        if resource["id"] not in {item["id"] for item in into["resources"]} and len(into["resources"]) < MAX_RESOURCES:
            into["resources"].append(resource)


def normalize_roadmap(value: Any, *, extra_sources: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Return validated roadmap items (possibly empty).

    Roadmap items nested inside another item's steps (older fallback reports)
    are lifted out as items of their own, and the container cards that had no
    steps of their own are dropped. Items for the same skill are merged; a
    step repeated on different skills stays only on the first.
    """

    queue: list[Any] = [*_list(value)]
    for source in extra_sources:
        queue += [entry for entry in _list(source) if _as_roadmap_dict(entry) is not None]
    collected: list[dict[str, Any]] = []
    budget = 50  # bounds work on malformed input
    while queue and budget:
        budget -= 1
        raw = _as_roadmap_dict(queue.pop(0))
        if raw is None:
            continue
        steps, nested = [], []
        for step in _list(raw.get("next_steps") if raw.get("next_steps") is not None else raw.get("steps")):
            inner = _as_roadmap_dict(step)
            if inner is not None:
                nested.append(inner)
                continue
            text = readable_text(step)
            if text:
                steps.append(text)
        if nested:
            queue = nested + queue
            if not steps:
                continue  # a container card: its content was the nested items
        item = _item(raw, steps)
        if item:
            collected.append(item)

    merged: dict[str, dict[str, Any]] = {}
    for item in collected:
        key = _skill_key(item["skill"])
        if key in merged:
            _merge(merged[key], item)
        else:
            merged[key] = item
    items = list(merged.values())
    # A step repeated on different skills is not specific to any of them
    # (older reports copied the same generic steps onto every card).
    owners: dict[str, int] = {}
    for item in items:
        for step in {_fingerprint(step) for step in item["next_steps"]}:
            owners[step] = owners.get(step, 0) + 1
    for item in items:
        item["next_steps"] = [step for step in item["next_steps"] if owners[_fingerprint(step)] == 1]
    # An item needs its own evidence or gap and at least one own step.
    return [item for item in items if item["next_steps"] and (item["evidence"] or item["gap"])][:MAX_ITEMS]


def normalize_review_items(value: Any) -> list[str]:
    """A clean, de-duplicated list of readable strings (never object text)."""

    items: list[str] = []
    seen: set[str] = set()
    for raw in _list(value):
        roadmap = _as_roadmap_dict(raw)
        if roadmap is not None:
            steps = [text for step in _list(roadmap.get("next_steps")) if (text := readable_text(step))]
            skill = readable_text(next((roadmap.get(key) for key in SKILL_KEYS if roadmap.get(key)), ""), 120)
            detail = steps[0] if steps else readable_text(roadmap.get("gap"), 300)
            text = f"{skill}: {detail}" if skill and detail else ""
        else:
            text = readable_text(raw)
        if text and _fingerprint(text) not in seen:
            seen.add(_fingerprint(text))
            items.append(text)
    return items


def normalize_report_evaluation(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Prepare a stored evaluation for display without changing the record.

    Scores, dimensions, submission details, and other fields are passed
    through unchanged. ``roadmap_status`` is "available", "unavailable" (a
    roadmap existed but nothing usable could be recovered), or "none".
    """

    report = deepcopy(evaluation)
    original = evaluation.get("personalized_roadmap")
    roadmap = normalize_roadmap(
        original,
        extra_sources=(evaluation.get("recommended_next_steps"), evaluation.get("recommended_skills")),
    )
    report["personalized_roadmap"] = roadmap
    for key in ("strengths", "areas_for_improvement", "recommended_next_steps", "recommended_skills"):
        if key in report:
            report[key] = normalize_review_items(report[key])
    had_roadmap = bool(_list(original)) or any(
        _as_roadmap_dict(entry) is not None
        for source in (evaluation.get("recommended_next_steps"), evaluation.get("recommended_skills"))
        for entry in _list(source)
    )
    report["roadmap_status"] = "available" if roadmap else "unavailable" if had_roadmap else "none"
    return report
