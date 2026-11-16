"""Predefined Backend Developer workplace scenario for the live demo.

The same validated project is the built-in fallback when task generation
cannot produce an assignment that passes the quality checks.
"""

from copy import deepcopy
from typing import Any

from services.ai.scenario_generation_service import validate_workplace_scenario


BACKEND_DEMO_CAREER_ID = "software-developer"
BACKEND_DEMO_POSITION_ID = "backend-developer"
BACKEND_DEMO_COMPANY_ID = "careergrid-demo"
BACKEND_DEMO_COMPANY_NAME = "TechNova"
BACKEND_DEMO_JOB_SOURCE = "backend_demo"


def is_backend_demo(
    career_id: str,
    position_id: str,
    company_id: str,
) -> bool:
    """Return whether the identifiers select the one predefined demo."""

    return (
        career_id == BACKEND_DEMO_CAREER_ID
        and position_id == BACKEND_DEMO_POSITION_ID
        and company_id == BACKEND_DEMO_COMPANY_ID
    )


def get_backend_demo_job() -> dict[str, str]:
    """Return browser-safe display data for the dedicated demo card."""

    return {
        "title": "Backend Developer — Demo Challenge",
        "company_id": BACKEND_DEMO_COMPANY_ID,
        "company_name": BACKEND_DEMO_COMPANY_NAME,
        "location": "Demo Environment",
        "description": (
            "Investigate and resolve related production API issues in a realistic "
            "backend development workspace."
        ),
        "job_source": BACKEND_DEMO_JOB_SOURCE,
    }


README = """# User Profile Service

## Overview

The User Profile Service is a small Flask API that TechNova's internal tools use to
show colleague profiles. It serves single profiles by ID and a paginated team
directory. Profile records live in `data/users.json`, which is a snapshot of the
HR system that is refreshed nightly. Accounts are never removed from the snapshot:
people who leave are deactivated (`"active": false`) and closed accounts are
soft-deleted (`"deleted_at"` holds a timestamp).

## Project structure

- `app.py` - application factory; registers the profile routes and error handlers.
- `api/profiles.py` - HTTP routes and query-parameter validation.
- `services/user_service.py` - loads records and implements lookup and directory listing.
- `services/visibility.py` - rules for which profiles appear in the directory and
  whether contact details may be shown.
- `serializers.py` - converts stored records into API responses.
- `errors.py` - `ApiError` and the JSON error format shared by every endpoint.
- `data/users.json` - sample records used by the service and the tests.
- `tests/test_profiles.py` - existing API tests written with pytest and the Flask test client.

## Expected behaviour

`GET /api/users/<user_id>` returns one available profile:

```http
GET /api/users/101
200 OK
{"id": 101, "name": "Amina Saleh", "team": "platform", "title": "Backend Engineer", "email": "amina@technova.test"}
```

Contact details are omitted when a person has `privacy.hide_contact` set. Profiles with
`"profile_visibility": "private"` are left out of the directory but can still be opened
directly by ID; this is intentional and must keep working.

`GET /api/users?team=<team>&page=<n>&page_size=<n>` returns a page of the team directory.
`page` starts at 1 and `page_size` is between 1 and 50 (default 20):

```http
GET /api/users?team=design&page=1&page_size=20
200 OK
{"items": [{"id": 207, "name": "Priya Shah", "title": "Product Designer"}, {"id": 212, "name": "Lena Fischer", "title": "UX Researcher"}],
 "page": 1, "page_size": 20, "total": 2}
```

`total` is the number of directory entries across all pages; the internal tools use it
to show "Showing 1-2 of 2".

Every error uses the same JSON shape and an appropriate status code:

```http
GET /api/users?page=0
400 Bad Request
{"error": {"code": "invalid_parameter", "message": "page must be a positive integer."}}
```

## Sample data and resources

`data/users.json` contains active, deactivated, soft-deleted, private, and
contact-hidden records across the `platform` and `design` teams. The task email
attaches `production-error.log` (failing requests captured in production),
`support-ticket-SUP-2291.md` (the directory problem reported by Customer Support), and
`profile-api-contract.md` (the agreed public contract for unavailable profiles).

## Verification

The existing tests in `tests/test_profiles.py` describe current behaviour. Add or update
tests for every behaviour you change, including edge cases.

CareerGrid's terminal cannot run Python or tests. Inside the workspace, verify by reading
the code paths and checking your expected results against `data/users.json` and the
examples above. In a local Python environment or in CI the suite runs with:

```bash
pip install flask pytest
pytest
```

In your handover, say which checks you reasoned through and which tests you wrote; do not
report tests as executed.

## Deliverables and handover

- Code changes that make the API meet the contract for unavailable profiles in both endpoints.
- Regression tests covering each reported case and the related edge cases.
- Your changes committed and pushed, either on a feature branch with a pull request or directly on main.
- A reply to the task email summarising what you found, what you changed, how you verified it, and any remaining risks.
"""

APP_PY = '''from flask import Flask

from api.profiles import profiles_bp
from errors import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.register_blueprint(profiles_bp)
    register_error_handlers(app)
    return app


app = create_app()
'''

PROFILES_PY = '''from flask import Blueprint, jsonify, request

from errors import ApiError
from serializers import to_directory_entry, to_public_profile
from services.user_service import find_user, list_users

profiles_bp = Blueprint("profiles", __name__)

MAX_PAGE_SIZE = 50


def _positive_int(raw_value, name, default, maximum=None):
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ApiError(400, "invalid_parameter", f"{name} must be a positive integer.")
    if value < 1 or (maximum is not None and value > maximum):
        raise ApiError(400, "invalid_parameter", f"{name} must be a positive integer.")
    return value


@profiles_bp.get("/api/users/<int:user_id>")
def get_user_profile(user_id):
    user = find_user(user_id)
    return jsonify(to_public_profile(user)), 200


@profiles_bp.get("/api/users")
def list_profiles():
    page = _positive_int(request.args.get("page"), "page", 1)
    page_size = _positive_int(request.args.get("page_size"), "page_size", 20, MAX_PAGE_SIZE)
    team = request.args.get("team") or None

    result = list_users(team=team, page=page, page_size=page_size)
    return jsonify(
        {
            "items": [to_directory_entry(user) for user in result["items"]],
            "page": page,
            "page_size": page_size,
            "total": result["total"],
        }
    ), 200
'''

USER_SERVICE_PY = '''import json
from pathlib import Path

from services.visibility import is_listed

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "users.json"


def load_users():
    with DATA_FILE.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def find_user(user_id):
    return next((user for user in load_users() if user["id"] == user_id), None)


def list_users(team=None, page=1, page_size=20):
    users = load_users()
    if team:
        users = [user for user in users if user.get("team") == team]

    total = len(users)
    listed = [user for user in users if is_listed(user)]
    start = (page - 1) * page_size
    return {"items": listed[start:start + page_size], "total": total}
'''

VISIBILITY_PY = '''"""Rules that decide how much of a profile other employees may see."""

DIRECTORY_VISIBILITY_LEVELS = {"public", "organization"}


def is_listed(user):
    """Return whether a profile may appear in the team directory."""
    return user.get("profile_visibility", "public") in DIRECTORY_VISIBILITY_LEVELS


def can_show_contact(user):
    """Return whether email may be included in profile responses."""
    return not user.get("privacy", {}).get("hide_contact", False)
'''

SERIALIZERS_PY = '''from services.visibility import can_show_contact


def to_public_profile(user):
    profile = {
        "id": user["id"],
        "name": user["name"],
        "team": user["team"],
        "title": user["title"],
    }
    if can_show_contact(user):
        profile["email"] = user["email"]
    return profile


def to_directory_entry(user):
    return {"id": user["id"], "name": user["name"], "title": user["title"]}
'''

ERRORS_PY = '''from flask import jsonify


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
'''

USERS_JSON = '''[
  {"id": 101, "name": "Amina Saleh", "team": "platform", "title": "Backend Engineer", "email": "amina@technova.test", "active": true, "profile_visibility": "public"},
  {"id": 103, "name": "Daniel Reed", "team": "platform", "title": "Site Reliability Engineer", "email": "daniel.reed@technova.test", "active": false, "profile_visibility": "public"},
  {"id": 118, "name": "Omar Haddad", "team": "platform", "title": "Data Engineer", "email": "omar.haddad@technova.test", "active": true, "deleted_at": "2026-07-30T09:12:00Z", "profile_visibility": "public"},
  {"id": 207, "name": "Priya Shah", "team": "design", "title": "Product Designer", "email": "priya@technova.test", "active": true, "profile_visibility": "organization", "privacy": {"hide_contact": true}},
  {"id": 212, "name": "Lena Fischer", "team": "design", "title": "UX Researcher", "email": "lena.fischer@technova.test", "active": true, "profile_visibility": "public"},
  {"id": 230, "name": "Marco Rossi", "team": "platform", "title": "Security Engineer", "email": "marco.rossi@technova.test", "active": true, "profile_visibility": "private"},
  {"id": 241, "name": "Sara Nasser", "team": "platform", "title": "Engineering Manager", "email": "sara.nasser@technova.test", "active": true, "profile_visibility": "public"}
]
'''

TESTS_PY = '''import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_active_profile_is_returned(client):
    response = client.get("/api/users/101")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Amina Saleh"
    assert response.get_json()["email"] == "amina@technova.test"


def test_hidden_contact_details_are_not_exposed(client):
    body = client.get("/api/users/207").get_json()

    assert body["name"] == "Priya Shah"
    assert "email" not in body


def test_private_profile_can_still_be_opened_directly(client):
    assert client.get("/api/users/230").status_code == 200


def test_directory_lists_design_team(client):
    body = client.get("/api/users?team=design").get_json()

    assert [entry["id"] for entry in body["items"]] == [207, 212]
    assert body["total"] == 2


def test_directory_rejects_invalid_page(client):
    response = client.get("/api/users?page=0")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_parameter"
'''

ERROR_LOG = """USER PROFILE API - PRODUCTION ERRORS (filtered)
2026-08-20

Case 1
GET /api/users/1842
Expected: 404 Not Found
Actual: 500 Internal Server Error
TypeError: 'NoneType' object is not subscriptable
Trace context: api/profiles.py get_user_profile -> serializers.py to_public_profile

Case 2
GET /api/users/103
Expected: 404 Not Found
Actual: 200 OK
Response contained the requested user profile.

Case 3
GET /api/users?team=platform&page=1&page_size=2
Actual: 200 OK
{"items": [{"id": 101, ...}, {"id": 103, ...}], "page": 1, "page_size": 2, "total": 5}
"""

SUPPORT_TICKET = """# SUP-2291 - Team directory shows people who have left

Reported by: Jordan Blake (Customer Support Lead)
Priority: High

The platform team page in the internal tools lists Daniel Reed, who left in June, and
Omar Haddad, whose account was closed at the end of July. Both open profile cards when
clicked. The header also says "Showing 1-4 of 5" even though only four cards appear,
and paging to page 2 with two people per page shows a page that does not add up.

The design team page looks correct.

Steps to reproduce:
1. Open the platform team directory (GET /api/users?team=platform).
2. Compare the people listed and the total with the current team roster.

Expected: only current employees with directory-visible profiles, and a total that
matches what can actually be paged through.
"""

API_CONTRACT = """# Profile API contract - unavailable profiles

Agreed with the Internal Tools team, version 1.3.

A profile is *unavailable* when the ID does not exist, the account is deactivated
(`active` is false), or the account is soft-deleted (`deleted_at` is set).

- `GET /api/users/<id>` for an unavailable profile returns 404 with:
  `{"error": {"code": "user_not_found", "message": "User not found."}}`
  The response must be identical for all three reasons, so callers cannot tell a
  deactivated account from an ID that never existed.
- The directory (`GET /api/users`) never includes unavailable profiles, and `total`
  counts only entries that can be returned across pages.
- A page beyond the last one returns `200` with an empty `items` list and the correct `total`.
- Private profiles (`profile_visibility: private`) stay out of the directory but remain
  available by ID. Contact-hiding rules are unchanged.
"""


def _scenario() -> dict[str, Any]:
    return {
        "public_scenario": {
            "scenario_id": "technova-user-profile-availability-v3",
            "title": "User Profile API Production Incident",
            "advisor": {
                "name": "Maya Chen",
                "title": "Senior Backend Engineer",
                "email": "maya.chen@technova.example",
            },
            "task": {
                "id": "user-profile-production-incident",
                "subject": "Production issue — User Profile API",
                "summary": (
                    "Unavailable profiles are handled inconsistently: unknown IDs crash, "
                    "deactivated and deleted accounts are still exposed, and the team "
                    "directory reports the wrong totals."
                ),
                "body": (
                    "Hi,\n\n"
                    "Support has escalated several related problems with the User Profile API.\n\n"
                    "Requests for user IDs that do not exist are returning 500 errors instead "
                    "of being handled gracefully, and a deactivated account is still accessible "
                    "through the public profile endpoint. Support ticket SUP-2291 adds that the "
                    "platform team directory lists people who have left and shows a total that "
                    "does not match the cards on screen.\n\n"
                    "Please investigate using production-error.log, support-ticket-SUP-2291.md, "
                    "and profile-api-contract.md (the contract we agreed with Internal Tools), and "
                    "read the README for how the service is organised. Bring both endpoints in line "
                    "with the contract without changing behaviour that is working today, such as "
                    "private profiles and hidden contact details. Add regression tests for what you "
                    "change.\n\n"
                    "When you are finished, reply with your findings, what you changed, how you "
                    "verified it, and where I can review it (a pull request link, or tell me it "
                    "is on main).\n\n"
                    "Thanks,\nMaya"
                ),
                "priority": "high",
                "deadline_minutes": 240,
                "attachments": [
                    "production-error-log",
                    "support-ticket",
                    "api-contract",
                ],
                "requirements": [
                    "GET /api/users/<id> returns the contract's 404 user_not_found error for IDs that do not exist instead of a 500.",
                    "Deactivated and soft-deleted accounts are treated as unavailable: the same 404 response by ID, and never listed in the directory.",
                    "The directory total counts only entries that can be returned across pages, and a page past the end returns an empty list with the correct total.",
                    "Existing behaviour is preserved: private profiles still open by ID but stay out of the directory, contact hiding is unchanged, and invalid query parameters still return 400.",
                ],
                "deliverables": [
                    "Code changes to the service committed and pushed",
                    "Regression tests for the reported cases and edge cases",
                    "A handover reply with findings, changes, verification, and the review location",
                ],
                "acceptance_criteria": [
                    "GET /api/users/1842, /api/users/103, and /api/users/118 each return 404 with error code user_not_found.",
                    "GET /api/users?team=platform lists only 101 and 241 with total 2.",
                    "GET /api/users/230 still returns 200, and /api/users/207 still omits email.",
                    "New tests cover missing, deactivated, and soft-deleted accounts plus the directory total.",
                ],
            },
            "background_emails": [
                {
                    "id": "api-support-context",
                    "sender_name": "Jordan Blake",
                    "sender_title": "Customer Support Lead",
                    "sender_email": "jordan.blake@technova.example",
                    "subject": "User profile error report",
                    "body": (
                        "Support reproduced separate failures with GET /api/users/1842 "
                        "and GET /api/users/103. The attached incident report records "
                        "the expected and actual responses for both cases, and SUP-2291 "
                        "covers the directory."
                    ),
                }
            ],
            "project": {
                "display_name": "User Profile Service",
                "name": "user-profile-service",
                "archive_name": "user-profile-service.zip",
                "default_branch": "main",
                "files": [
                    {"path": "README.md", "content": README},
                    {"path": "app.py", "content": APP_PY},
                    {"path": "api/__init__.py", "content": '"""HTTP routes for the User Profile Service."""\n'},
                    {"path": "api/profiles.py", "content": PROFILES_PY},
                    {"path": "services/__init__.py", "content": '"""Domain services for profile data."""\n'},
                    {"path": "services/user_service.py", "content": USER_SERVICE_PY},
                    {"path": "services/visibility.py", "content": VISIBILITY_PY},
                    {"path": "serializers.py", "content": SERIALIZERS_PY},
                    {"path": "errors.py", "content": ERRORS_PY},
                    {"path": "data/users.json", "content": USERS_JSON},
                    {"path": "tests/test_profiles.py", "content": TESTS_PY},
                ],
            },
            "resources": [
                {"id": "production-error-log", "name": "production-error.log", "type": "text", "content": ERROR_LOG},
                {"id": "support-ticket", "name": "support-ticket-SUP-2291.md", "type": "text", "content": SUPPORT_TICKET},
                {"id": "api-contract", "name": "profile-api-contract.md", "type": "text", "content": API_CONTRACT},
            ],
            "skill_targets": [
                "reading production error evidence",
                "tracing request and data flow across modules",
                "HTTP status-code and API-contract reasoning",
                "access-control and data-availability reasoning",
                "pagination edge cases",
                "preserving existing behaviour",
                "writing regression tests",
                "Git workflow",
                "professional communication",
            ],
        },
        "private_context": {
            "root_cause": (
                "There are three connected causes. find_user returns None for user ID 1842 "
                "and the route passes it straight to to_public_profile, which subscripts it "
                "without guarding the missing-user case, raising TypeError and producing HTTP 500. "
                "find_user matches only by ID, so it returns the deactivated user 103 and the "
                "soft-deleted user 118 as available profiles. list_users filters only by "
                "directory visibility, so inactive and deleted users are listed, and it "
                "computes total before filtering, so the private profile 230 and unavailable "
                "users inflate the total."
            ),
            "expected_changes": [
                {
                    "path": "services/visibility.py",
                    "expectation": (
                        "Introduce one availability rule (active and not soft-deleted) that both "
                        "lookup and directory use, separate from directory visibility."
                    ),
                },
                {
                    "path": "services/user_service.py",
                    "expectation": (
                        "Lookup treats deactivated users and soft-deleted users as unavailable while "
                        "still returning private profiles by ID; the directory filters unavailable "
                        "and unlisted users before computing total and slicing, preserving lookup "
                        "behavior for active users."
                    ),
                },
                {
                    "path": "api/profiles.py",
                    "expectation": (
                        "Raise ApiError(404, 'user_not_found', 'User not found.') when no available "
                        "user is found so missing, deactivated, and deleted IDs get the same HTTP 404 "
                        "JSON response; preserve the existing successful 200 response for known users."
                    ),
                },
                {
                    "path": "tests/test_profiles.py",
                    "expectation": (
                        "Add regression tests for 1842, 103, and 118 returning 404 user_not_found, "
                        "the platform directory listing only 101 and 241 with total 2, and a page "
                        "past the end."
                    ),
                },
            ],
            "acceptable_alternatives": [
                "Filter inactive and deleted records directly inside find_user and handle its None result in the route.",
                "Raise a focused not-found exception from the service and translate it to the 404 JSON response in the route.",
                "Implement availability in user_service.py instead of visibility.py, as long as lookup and directory share it.",
                "Do not accept broad exception handling that converts unexpected unrelated server failures into HTTP 404 responses.",
                "Do not accept reusing is_listed in find_user, because it would hide private profile 230 from direct lookup.",
            ],
            "verification_expectations": [
                "Case A: explain or demonstrate that active user 101 still returns the profile with HTTP 200.",
                "Case B: explain or demonstrate that nonexistent user 1842 returns HTTP 404 with a clear JSON error response.",
                "Case C: explain or demonstrate that deactivated user 103 returns HTTP 404 and no inactive profile data is exposed.",
                "Case D: soft-deleted user 118 returns HTTP 404 and is absent from the directory.",
                "Case E: the platform directory returns 101 and 241 with total 2; a page past the end returns an empty list.",
                "Private profile 230 still opens by ID and 207 still hides email.",
                "Verification is described honestly as reasoning and written tests, not as executed tests.",
            ],
            "assessment_criteria": [
                {
                    "id": "missing_user_404",
                    "criterion": "Unknown IDs return the contract 404 instead of crashing.",
                    "evidence": "The route or service handles a missing user before serialization and raises ApiError(404, 'user_not_found', ...).",
                    "files": ["api/profiles.py", "services/user_service.py"],
                    "requirement_refs": [1],
                },
                {
                    "id": "unavailable_accounts",
                    "criterion": "Deactivated and soft-deleted accounts are unavailable by ID and in the directory.",
                    "evidence": "A shared availability rule checks active and deleted_at and is used by lookup and listing.",
                    "files": ["services/visibility.py", "services/user_service.py"],
                    "requirement_refs": [2],
                },
                {
                    "id": "directory_total",
                    "criterion": "Directory total and paging reflect only returnable entries.",
                    "evidence": "Filtering happens before total is computed and before slicing.",
                    "files": ["services/user_service.py"],
                    "requirement_refs": [3],
                },
                {
                    "id": "preserved_behaviour",
                    "criterion": "Private-profile, contact-hiding, and validation behaviour is unchanged.",
                    "evidence": "find_user does not use is_listed; serializers and _positive_int keep their behaviour; existing tests still hold.",
                    "files": ["services/user_service.py", "serializers.py", "api/profiles.py"],
                    "requirement_refs": [4],
                },
                {
                    "id": "regression_tests",
                    "criterion": "Regression tests cover each reported case and edge case.",
                    "evidence": "tests/test_profiles.py gains tests for 1842, 103, 118, the platform directory total, and an out-of-range page.",
                    "files": ["tests/test_profiles.py"],
                    "requirement_refs": [1, 2, 3],
                },
            ],
            "starter_gap_checks": [
                {
                    "id": "not_found_error",
                    "any_of": [
                        {"file": "api/profiles.py", "must_include_any": ["user_not_found", "ApiError(404"]},
                        {"file": "services/user_service.py", "must_include_any": ["user_not_found", "ApiError(404"]},
                    ],
                },
                {
                    "id": "inactive_excluded",
                    "any_of": [
                        {"file": "services/visibility.py", "must_include_any": ["\"active\"", "'active'"]},
                        {"file": "services/user_service.py", "must_include_any": ["\"active\"", "'active'"]},
                    ],
                },
                {
                    "id": "deleted_excluded",
                    "any_of": [
                        {"file": "services/visibility.py", "must_include_any": ["deleted_at"]},
                        {"file": "services/user_service.py", "must_include_any": ["deleted_at"]},
                    ],
                },
                {
                    "id": "regression_tests_added",
                    "any_of": [
                        {"file": "tests/test_profiles.py", "must_include_any": ["404", "user_not_found"]},
                    ],
                },
            ],
            "progressive_guidance": [
                {
                    "level": 1,
                    "guidance": (
                        "Compare each reported request with the records in data/users.json, then "
                        "trace the request from api/profiles.py through the service to the serializer."
                    ),
                },
                {
                    "level": 2,
                    "guidance": (
                        "Look at what the lookup returns when nothing matches, which record fields "
                        "the lookup and the directory consider, and the order in which list_users "
                        "counts and filters records. Note that directory visibility and account "
                        "availability are different questions."
                    ),
                },
                {
                    "level": 3,
                    "guidance": (
                        "Define availability once (active and not deleted), use it in both lookup and "
                        "listing, translate 'no available user' into the contract's 404 error in the "
                        "route, and count the directory total after filtering."
                    ),
                },
            ],
            "evaluation_notes": {
                "difficulty": "junior",
                "important_evidence": [
                    "The changed code guards the missing-user path before serializing the lookup result.",
                    "Deactivated and soft-deleted users are unavailable by ID and in the directory.",
                    "The directory total is computed after filtering.",
                    "Private profile 230 remains reachable by ID and contact hiding is unchanged.",
                    "The implementation does not swallow unrelated exceptions as not-found responses.",
                    "Regression tests cover the reported cases and edge cases.",
                    "The submission includes coherent Git and communication evidence.",
                ],
            },
        },
    }


def get_backend_demo_workplace_scenario(
    *,
    attempt_id: str,
) -> dict[str, dict[str, Any]]:
    """Build and validate the fixed TechNova production incident."""

    # The scenario content is deliberately stable between presentation runs.
    # The attempt ID remains part of the function contract for parity with the
    # generated scenario services and future versioning needs.
    _ = attempt_id
    return validate_workplace_scenario(_scenario())


def get_backend_fallback_scenario(*, attempt_id: str) -> dict[str, dict[str, Any]]:
    """The validated built-in assignment used when generation fails."""

    scenario = deepcopy(get_backend_demo_workplace_scenario(attempt_id=attempt_id))
    scenario["public_scenario"]["scenario_id"] = f"technova-user-profile-fallback-{attempt_id}"
    return scenario
