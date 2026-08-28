"""Predefined Backend Developer workplace scenario for the live demo."""

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


def get_backend_demo_workplace_scenario(
    *,
    attempt_id: str,
) -> dict[str, dict[str, Any]]:
    """Build and validate the fixed TechNova production incident."""

    # The scenario content is deliberately stable between presentation runs.
    # The attempt ID remains part of the function contract for parity with the
    # generated scenario services and future versioning needs.
    _ = attempt_id

    scenario = {
        "public_scenario": {
            "scenario_id": "technova-user-profile-availability-v2",
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
                    "Investigate two reported availability and access problems "
                    "affecting the public User Profile API."
                ),
                "body": (
                    "Hi,\n\n"
                    "Support has reported two issues with the User Profile API.\n\n"
                    "First, requests for user IDs that do not exist are returning "
                    "500 errors instead of being handled gracefully.\n\n"
                    "Second, a deactivated account is still accessible through "
                    "the public profile endpoint.\n\n"
                    "Please investigate both cases, review the available evidence, "
                    "implement a focused fix, and prepare the change for review. "
                    "The API should handle unavailable profiles safely without "
                    "exposing deactivated accounts.\n\n"
                    "When you are finished, send me your findings, what you changed, "
                    "how you verified the behavior, and the pull request link.\n\n"
                    "Thanks,\nMaya"
                ),
                "priority": "high",
                "deadline_minutes": 240,
                "attachments": ["production-error-log"],
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
                        "the expected and actual responses for both cases."
                    ),
                }
            ],
            "project": {
                "display_name": "User Profile Service",
                "name": "user-profile-service",
                "archive_name": "user-profile-service.zip",
                "default_branch": "main",
                "files": [
                    {
                        "path": "README.md",
                        "content": (
                            "# User Profile Service\n\n"
                            "This small Flask service exposes user profile data to "
                            "internal TechNova applications.\n\n"
                            "## Endpoint\n\n"
                            "`GET /api/users/<user_id>` returns a JSON profile when "
                            "the user is available. If the requested profile does "
                            "not exist or is unavailable, the endpoint should return "
                            "a JSON error with HTTP 404. Deactivated profiles must "
                            "not be exposed through this public endpoint.\n\n"
                            "## Project structure\n\n"
                            "- `app.py` defines the HTTP route.\n"
                            "- `services/user_service.py` performs the user lookup.\n"
                            "- `data/users.json` contains the local demo records.\n"
                        ),
                    },
                    {
                        "path": "app.py",
                        "content": (
                            "from flask import Flask, jsonify\n\n"
                            "from services.user_service import find_user\n\n\n"
                            "app = Flask(__name__)\n\n\n"
                            "@app.get(\"/api/users/<int:user_id>\")\n"
                            "def get_user_profile(user_id):\n"
                            "    user = find_user(user_id)\n\n"
                            "    profile = {\n"
                            "        \"id\": user[\"id\"],\n"
                            "        \"name\": user[\"name\"],\n"
                            "        \"email\": user[\"email\"],\n"
                            "    }\n\n"
                            "    return jsonify(profile), 200\n"
                        ),
                    },
                    {
                        "path": "services/user_service.py",
                        "content": (
                            "import json\n"
                            "from pathlib import Path\n\n\n"
                            "DATA_FILE = Path(__file__).parent.parent / \"data\" / \"users.json\"\n\n\n"
                            "def load_users():\n"
                            "    with DATA_FILE.open(encoding=\"utf-8\") as data_file:\n"
                            "        return json.load(data_file)\n\n\n"
                            "def find_user(user_id):\n"
                            "    return next(\n"
                            "        (\n"
                            "            user\n"
                            "            for user in load_users()\n"
                            "            if user[\"id\"] == user_id\n"
                            "        ),\n"
                            "        None,\n"
                            "    )\n"
                        ),
                    },
                    {
                        "path": "data/users.json",
                        "content": (
                            "[\n"
                            "  {\"id\": 101, \"name\": \"Amina Saleh\", \"email\": \"amina@technova.test\", \"active\": true},\n"
                            "  {\"id\": 103, \"name\": \"Daniel Reed\", \"email\": \"daniel.reed@technova.test\", \"active\": false},\n"
                            "  {\"id\": 207, \"name\": \"Priya Shah\", \"email\": \"priya@technova.test\", \"active\": true}\n"
                            "]\n"
                        ),
                    },
                ],
            },
            "resources": [
                {
                    "id": "production-error-log",
                    "name": "production-error.log",
                    "type": "text",
                    "content": (
                        "USER PROFILE API SUPPORT REPORT\n"
                        "2026-08-20\n\n"
                        "Case 1\n"
                        "GET /api/users/1842\n"
                        "Expected: 404 Not Found\n"
                        "Actual: 500 Internal Server Error\n"
                        "TypeError: 'NoneType' object is not subscriptable\n"
                        "Trace context: app.py, get_user_profile\n\n"
                        "Case 2\n"
                        "GET /api/users/103\n"
                        "Expected: 404 Not Found\n"
                        "Actual: 200 OK\n"
                        "Response contained the requested user profile.\n"
                    ),
                }
            ],
            "skill_targets": [
                "reading production error evidence",
                "debugging",
                "tracing request and data flow",
                "HTTP status-code reasoning",
                "defensive backend programming",
                "access-control and data-availability reasoning",
                "focused code modification",
                "verification reasoning",
                "Git workflow",
                "professional communication",
            ],
        },
        "private_context": {
            "root_cause": (
                "There are two related causes. First, find_user returns None for "
                "user ID 1842, but the route reads id, name, and email from that "
                "value without guarding the missing-user case, raising TypeError "
                "and producing HTTP 500. Second, find_user matches only by ID, so "
                "it returns the deactivated user 103 as an available profile and "
                "the route exposes that profile with HTTP 200."
            ),
            "expected_changes": [
                {
                    "path": "app.py",
                    "expectation": (
                        "Handle the None result before accessing user fields and "
                        "return a clean JSON error such as {'error': 'User not "
                        "found'} with HTTP 404; preserve the existing successful "
                        "200 response for known users."
                    ),
                },
                {
                    "path": "services/user_service.py",
                    "expectation": (
                        "Make the profile lookup treat deactivated users as "
                        "unavailable so user 103 is not returned as a normal public "
                        "profile, while preserving lookup behavior for active users."
                    ),
                }
            ],
            "acceptable_alternatives": [
                "Filter inactive records directly inside find_user and handle its None result in the route.",
                "Reject inactive records in another clearly separated service method that returns no available user to the route.",
                "Raise a focused not-found or unavailable-user exception from the service and translate it to a 404 JSON response in the route.",
                "Use an equivalent JSON error message as long as both missing and inactive profiles return 404 without exposing profile data.",
                "Do not accept broad exception handling that converts unexpected unrelated server failures into HTTP 404 responses.",
            ],
            "verification_expectations": [
                "Case A: explain or demonstrate that active user 101 still returns the profile with HTTP 200.",
                "Case B: explain or demonstrate that nonexistent user 1842 returns HTTP 404 with a clear JSON error response.",
                "Case C: explain or demonstrate that deactivated user 103 returns HTTP 404 and no inactive profile data is exposed.",
                "Keep the change focused and prepare it on a separate Git branch with a meaningful commit and pull request.",
            ],
            "progressive_guidance": [
                {
                    "level": 1,
                    "guidance": (
                        "Compare both reported requests with the stored user data, "
                        "then trace the profile flow from the route through the lookup."
                    ),
                },
                {
                    "level": 2,
                    "guidance": (
                        "Inspect what the user lookup returns when no record "
                        "matches the requested ID, and inspect which record attributes "
                        "the lookup considers when deciding a profile is available."
                    ),
                },
                {
                    "level": 3,
                    "guidance": (
                        "The route should safely handle a lookup result representing "
                        "no available user, and the lookup should not return "
                        "deactivated profiles as valid public profiles."
                    ),
                },
            ],
            "evaluation_notes": {
                "difficulty": "junior",
                "important_evidence": [
                    "The changed code guards the missing-user path before subscripting the lookup result.",
                    "The service no longer returns user 103 or another inactive record as an available public profile.",
                    "Both missing and inactive users receive a controlled HTTP 404 JSON response.",
                    "The active-user HTTP 200 profile path remains intact.",
                    "The implementation is focused and does not swallow unrelated exceptions as not-found responses.",
                    "The submission includes coherent Git and communication evidence.",
                ],
            },
        },
    }

    return validate_workplace_scenario(scenario)
