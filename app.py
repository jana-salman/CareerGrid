from flask import Flask, render_template, redirect, url_for, session, request
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from routes.auth import auth_bp

from services.simulation_generator import (
    generate_backend_inbox_task,
    generate_frontend_inbox_task,
)
from services.roadmap_service import (
    RoadmapGenerationError,
    generate_personalized_roadmap,
)
from services.evaluation_service import (
    SimulationEvaluationError,
    evaluate_simulation,
)
from services.inbox_response_service import (
    InboxResponseValidationError,
    validate_inbox_response,
)

from services.simulation_storage import (
    save_simulation_step_response,
    create_backend_simulation_attempt,
    create_frontend_simulation_attempt,
    get_backend_inbox_task,
    save_simulation_evaluation,
    save_simulation_roadmap,
    get_simulation_attempt,
    list_completed_simulation_attempts,
)

from services.incident_response_service import (
    IncidentResponseValidationError,
    validate_incident_response,
)

from services.code_lab_response_service import (
    CodeLabResponseValidationError,
    validate_code_lab_response,
)
from services.api_testing_response_service import (
    ApiTestingResponseValidationError,
    validate_api_testing_response,
)

from services.team_chat_response_service import (
    TeamChatResponseValidationError,
    validate_team_chat_response,
)


from services.frontend_investigation_response_service import (
    FrontendInvestigationValidationError,
    validate_frontend_investigation_response,
)

from services.frontend_code_lab_response_service import (
    FrontendCodeLabValidationError,
    validate_frontend_code_lab_response,
)

from services.frontend_browser_testing_response_service import (
    FrontendBrowserTestingValidationError,
    validate_frontend_browser_testing_response,
)

from services.frontend_team_chat_response_service import (
    FrontendTeamChatValidationError,
    validate_frontend_team_chat_response,
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

    if (
        request.endpoint not in PUBLIC_ROUTES
        and "user_email" not in session
    ):
        return redirect(url_for("auth.login"))

# =========================================================
# SIMULATION STEP 1
# =========================================================

SIMULATION_DATA = {
    "software-developer": {


        "frontend-developer": {
            "sender": "Maya Lewis, Frontend Team Lead",

            "subject": "Buy Now button is not responding",

            "body": (
                "Several users reported that clicking the Buy Now button "
                "does not open the checkout page. The issue appears on "
                "some product pages. Please investigate the frontend "
                "behavior and determine what prevents the button from working."
            )
        }
    }
}


# =========================================================
# SIMULATION STEP 2
# =========================================================

STEP_TWO_TASKS = {
    "software-developer": {

        "frontend-developer": {
            "title": "Review the Browser Error",

            "instructions": (
                "The frontend team reproduced the button problem and "
                "found the following message in the browser console."
            ),

            "log": (
                "Uncaught TypeError: Cannot read properties of null\n"
                "at product.js:42\n\n"
                "const checkoutButton = "
                "document.querySelector('#checkout-button');\n"
                "checkoutButton.addEventListener('click', handleBuyNow);"
            ),

            "question": (
                "What does this browser error suggest, and what HTML "
                "element or JavaScript code would you inspect first?"
            )
        }
    }
}


# =========================================================
# SIMULATION STEP 3
# =========================================================

STEP_THREE_TASKS = {
    "software-developer": {


        "frontend-developer": {
            "title": "Choose the Best Frontend Fix",

            "instructions": (
                "The browser cannot find the checkout button, so "
                "querySelector returns null. Review the possible fixes."
            ),

            "code": (
                "const checkoutButton = "
                "document.querySelector('#checkout-button');\n\n"
                "checkoutButton.addEventListener(\n"
                "    'click',\n"
                "    handleBuyNow\n"
                ");"
            ),

            "question": "Which frontend solution would you choose?",

            "options": [
                {
                    "value": "option_a",

                    "label": (
                        "Run the same code repeatedly until the button "
                        "is eventually found."
                    )
                },

                {
                    "value": "option_b",

                    "label": (
                        "Confirm the selector is correct, wait until the "
                        "page content is loaded, and check that the element "
                        "exists before attaching the event listener."
                    )
                },

                {
                    "value": "option_c",

                    "label": (
                        "Remove the Buy Now button from the product page "
                        "so the JavaScript error stops appearing."
                    )
                }
            ]
        }
    }
}


# =========================================================
# SIMULATION STEP 4
# =========================================================

STEP_FOUR_TASKS = {
    "software-developer": {

        "frontend-developer": {
            "title": "Implement a Safer Frontend Fix",

            "instructions": (
                "You decided to check that the checkout button exists "
                "before attaching its click event."
            ),

            "code": (
                "const checkoutButton = "
                "document.querySelector('#checkout-button');\n\n"
                "checkoutButton.addEventListener(\n"
                "    'click',\n"
                "    handleBuyNow\n"
                ");"
            ),

            "question": (
                "Write a safer version of this JavaScript code, or clearly "
                "explain the exact changes you would make."
            ),

            "placeholder": (
                "Example: find the button after the page loads, check "
                "whether it exists, and only then add the event listener..."
            )
        }
    }
}


# =========================================================
# SIMULATION STEP 5
# =========================================================

STEP_FIVE_TASKS = {
    "software-developer": {


        "frontend-developer": {
            "title": "Send a Frontend Update",

            "instructions": (
                "You identified why the Buy Now button was not working "
                "and prepared a safer frontend fix. Your team lead wants "
                "a short status update."
            ),

            "message": (
                "Explain what caused the browser error, what you changed "
                "in the frontend, and what should be tested before release."
            ),

            "question": (
                "Write a clear update that you would send to your "
                "frontend team lead."
            ),

            "placeholder": (
                "Example: The JavaScript selector could not find the "
                "checkout button, so the code tried to attach an event "
                "listener to null..."
            )
        }
    }
}

# =========================================================
# COMPLETE BACKEND SIMULATION SCENARIO
# =========================================================

BACKEND_SCENARIO = {
    "scenario_id": "checkout-api-investigation",
    "career_id": "software-developer",
    "position_id": "backend-developer",
    "title": "Checkout API Investigation",
    "evaluation": {
        1: {
            "skill": "Problem Investigation",
            "keywords": [
                "payload",
                "request",
                "cart",
                "logs",
                "reproduce",
                "backend"
            ]
        },

        2: {
            "skill": "Error Analysis",
            "keywords": [
                "product_id",
                "missing",
                "keyerror",
                "payload",
                "cart item"
            ]
        },

        3: {
            "skill": "Technical Decision Making",
            "correct_answer": "option_b"
        },

        4: {
            "skill": "Input Validation",
            "keywords": [
                "get",
                "product_id",
                "validate",
                "missing",
                "400",
                "error"
            ]
        },

        5: {
            "skill": "Technical Communication",
            "keywords": [
                "500",
                "product_id",
                "validation",
                "400",
                "test",
                "payload"
            ]
        }
    },
   
    "steps": {
        1: {
            "sender": "Alex Carter, Backend Team Lead",

            "subject": "Intermittent 500 error from checkout API",

            "body": (
                "The POST /api/checkout endpoint is failing for some customers, "
                "while other checkout requests complete successfully. The problem "
                "appears only with certain cart payloads. Please investigate the "
                "request data and the backend checkout logic before today's release."
            )
        },

        2: {
            "title": "Review the Checkout API Error",

            "instructions": (
                "After reproducing the failure with one of the affected cart "
                "payloads, the backend team captured the following server log."
            ),

            "log": (
                "[10:42:18] POST /api/checkout 500\n"
                "KeyError: 'product_id'\n"
                'File "checkout_service.py", line 84, in create_order\n'
                'product_id = item["product_id"]'
            ),

            "question": (
                "What does this error indicate about the cart request payload, "
                "and which data would you inspect first?"
            )
        },

        3: {
            "title": "Choose the Best Checkout API Fix",

            "instructions": (
                "The failed cart payload is missing product_id for one item. "
                "The checkout service currently accesses that field directly, "
                "which causes the POST /api/checkout request to return a 500 error."
            ),

            "code": (
                "for item in cart_items:\n"
                '    product_id = item["product_id"]\n'
                "    create_order_item(product_id)"
            ),

            "question": (
                "Which solution would best prevent the checkout API from crashing?"
            ),

            "options": [
                {
                    "value": "option_a",
                    "label": (
                        "Keep the code unchanged and ask the customer "
                        "to submit the checkout request again."
                    )
                },
                {
                    "value": "option_b",
                    "label": (
                        "Validate product_id before using it and return a clear "
                        "400 error when the cart payload is invalid."
                    )
                },
                {
                    "value": "option_c",
                    "label": (
                        "Catch every exception and continue creating the order "
                        "without the invalid cart item."
                    )
                }
            ]
        },

        4: {
            "title": "Implement the Checkout API Validation",

            "instructions": (
                "Input validation is the recommended solution for this checkout "
                "API problem. Update the checkout service so a missing product_id "
                "produces a clear client error instead of an internal server error."
            ),

            "code": (
                "for item in cart_items:\n"
                '    product_id = item["product_id"]\n'
                "    create_order_item(product_id)"
            ),

            "question": (
                "Write a safer version of this Python code, or explain exactly "
                "how you would validate the cart payload."
            ),

            "placeholder": (
                "Use item.get('product_id'), check whether the value exists, "
                "and return a clear 400 response when the payload is invalid..."
            )
        },

        5: {
            "title": "Report the Checkout API Fix",

            "instructions": (
                "The checkout service now validates each cart item before "
                "creating the order. Your backend team lead wants a final update."
            ),

            "message": (
                "Explain why POST /api/checkout returned a 500 error, "
                "how the validation fixed it, and which cases should be tested "
                "before the change is released."
            ),

            "question": (
                "Write the update you would send to your backend team lead."
            ),

            "placeholder": (
                "The checkout API failed because some cart items were missing "
                "product_id. The service accessed that field directly..."
            )
        }
    }
}

# =========================================================
# POSITION AND COMPANY DATA
# =========================================================
FRONTEND_SCENARIO = {
    "scenario_id": "buy-now-button-fix",
    "career_id": "software-developer",
    "position_id": "frontend-developer",
    "title": "Buy Now Button Fix",

    "steps": {
        1: {
            "sender": "Maya Lewis, Frontend Team Lead",
            "subject": "Buy Now button not opening checkout",
            "body": (
                "After the latest product-page deployment, the Buy Now "
                "button no longer opens the checkout panel for some "
                "users, especially on smaller screens. Please "
                "investigate and fix it before the next release."
            ),
        },

        2: {
            "title": "Investigate the Buy Now Button in DevTools",
            "issue_id": "FE-4021",
            "instructions": (
                "Inspect the console error, the Elements panel HTML, and "
                "the failing selector. Compare the button's HTML id with "
                "the selector used in product.js and identify why "
                "querySelector returns null and addEventListener fails."
            ),
            "root_cause": (
                "The HTML id is buy-now-btn but product.js queries "
                "#checkout-btn, so querySelector returns null and "
                "addEventListener is called on null."
            ),
        },

        3: {
            "title": "Fix the Buy Now Button",
            "issue_id": "FE-4021",
            "instructions": (
                "Update product.js so it selects the correct button "
                "(buy-now-btn), initializes after the DOM is ready, "
                "checks the element exists, and attaches the checkout "
                "click handler."
            ),
        },

        4: {
            "title": "Test the Buy Now Button in the Browser",
            "instructions": (
                "Run the desktop mouse test, the mobile viewport test, "
                "and the keyboard and accessibility test, then make a "
                "release decision."
            ),
            "required_tests": [
                "desktop_mouse",
                "mobile_viewport",
                "keyboard_accessibility",
            ],
        },

        5: {
            "title": "Send the Frontend Release Update",
            "channel": "frontend-releases",
            "recipient": "Maya Lewis, Frontend Team Lead",
            "issue_id": "FE-4021",
            "instructions": (
                "Post a professional update covering issue status, the "
                "completed checklist, root cause, fix summary, "
                "browser-testing summary, accessibility and "
                "responsive-design summary, and a release recommendation."
            ),
        },
    },
}



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
    }
}


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
            timeout=5
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
    return render_template("home.html")


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

    jobs = fetch_adzuna_jobs(position_title)

    return render_template(
        "companies.html",
        career_id=career_id,
        career_name=career_name,
        position_id=position_id,
        position_title=position_title,
        jobs=jobs,
        local_companies=local_companies
    )

def prepare_answers_for_evaluation(answers):
    """
    Convert JSON answer strings back into dictionaries when possible.
    """

    prepared_answers = {}

    for key, value in answers.items():
        if isinstance(value, str):
            try:
                prepared_answers[key] = json.loads(value)
            except json.JSONDecodeError:
                prepared_answers[key] = value
        else:
            prepared_answers[key] = value

    return prepared_answers

# Human-readable skill names for each simulation step, used on the
# results page so the user sees which specific skill needs practice.
FRONTEND_STEP_SKILLS = [
    "Inbox Prioritization & Communication",
    "DevTools Debugging",
    "Fixing DOM & Event Code",
    "Browser & Accessibility Testing",
    "Technical Communication",
]

BACKEND_STEP_SKILLS = [
    "Inbox Prioritization & Communication",
    "Incident Investigation",
    "Technical Decision Making",
    "API Validation & Testing",
    "Technical Communication",
]

# A step is considered "ready" at or above this score, otherwise the
# user is told to practice that specific skill more.
STEP_READY_THRESHOLD = 70


def _step_skill_names(position_id=None, scenario_id=None):
    """Return the list of step skill names for a simulation, or None."""

    if (
        position_id == "frontend-developer"
        or scenario_id == "buy-now-button-fix"
    ):
        return FRONTEND_STEP_SKILLS

    if (
        position_id == "backend-developer"
        or scenario_id == "checkout-api-investigation"
    ):
        return BACKEND_STEP_SKILLS

    return None


def _build_readiness(score):
    """
    Turn the overall score into a clear readiness verdict shown at
    the top of the results page.
    """

    if score >= 80:
        return {
            "ready": True,
            "label": "Ready to apply",
            "headline": "You're ready to apply for this role.",
            "advice": (
                "Your performance shows you can handle this role's "
                "core tasks. Keep the roadmap below as a refresher."
            ),
        }

    if score >= 60:
        return {
            "ready": False,
            "label": "Almost ready",
            "headline": "Almost there — a little more practice.",
            "advice": (
                "You have a solid foundation. Focus on the skills "
                "marked 'Needs practice' below, then you'll "
                "be ready to apply."
            ),
        }

    return {
        "ready": False,
        "label": "Needs more practice",
        "headline": "Practice more before applying.",
        "advice": (
            "Work through the roadmap below, especially the skills "
            "marked 'Needs practice', then retry the "
            "simulation."
        ),
    }


def prepare_evaluation_for_results_page(
    evaluation,
    skill_names=None,
):
    """
    Convert Gemini evaluation fields into the format expected
    by the current roadmap template.

    skill_names:
        Optional list of five human-readable skill names, one per
        simulation step. When provided, each step shows its real
        skill name and a "ready" / "needs practice" status.
    """

    if not isinstance(evaluation, dict):
        return None

    score = evaluation.get(
        "overall_score",
        0,
    )

    if score >= 80:
        performance_level = "Strong"
    elif score >= 60:
        performance_level = "Developing"
    else:
        performance_level = "Needs Practice"

    step_results = []

    for step_feedback in evaluation.get(
        "step_feedback",
        [],
    ):
        step_number = step_feedback.get("step")
        step_score = step_feedback.get("score", 0)

        if (
            skill_names
            and isinstance(step_number, int)
            and 1 <= step_number <= len(skill_names)
        ):
            skill_name = skill_names[step_number - 1]
        else:
            skill_name = f"Simulation Step {step_number}"

        step_results.append({
            "step": step_number,
            "skill": skill_name,
            "score": step_score,
            "maximum_score": 100,
            "status": (
                "ready"
                if step_score >= STEP_READY_THRESHOLD
                else "needs_practice"
            ),
            "feedback": step_feedback.get(
                "feedback",
                "",
            ),
        })

    # Skills to practice more, based on low-scoring steps.
    skills_to_practice = [
        step["skill"]
        for step in step_results
        if step["status"] == "needs_practice"
    ]

    return {
        "score": score,
        "maximum_score": 100,
        "performance_level": performance_level,
        "readiness": _build_readiness(score),
        "summary": evaluation.get(
            "summary",
            "",
        ),
        "strengths": evaluation.get(
            "strengths",
            [],
        ),
        "skills_to_improve": evaluation.get(
            "areas_for_improvement",
            [],
        ),
        "recommended_skills": evaluation.get(
            "recommended_skills",
            [],
        ),
        "skills_to_practice": skills_to_practice,
        "step_results": step_results,
    }
# =========================================================
# SIMULATION ROUTE
# =========================================================

@app.route(
    "/simulation/<career_id>/<position_id>/<company_id>/<int:step>",
    methods=["GET", "POST"]
)
def simulation_step(career_id, position_id, company_id, step):
    """
    GET:
        Display the current simulation step.

    POST:
        Receive the user's answer, save it in the session,
        and redirect to the next step.
    """

    total_steps = 5

    # Prevent invalid step numbers such as 0 or 6.
    if step < 1 or step > total_steps:
        return redirect(
            url_for(
                "simulation_step",
                career_id=career_id,
                position_id=position_id,
                company_id=company_id,
                step=1
            )
        )

    career_name = career_id.replace("-", " ").title()
    company_name = company_id.replace("-", " ").title()

    # Get the selected position information.
    position_data = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    position_title = position_data.get("title", "")

    # Get the correct tasks based on career and position.
    # Get the correct tasks based on career and position.
    if (
        career_id == BACKEND_SCENARIO["career_id"]
        and position_id == BACKEND_SCENARIO["position_id"]
    ):
        scenario = BACKEND_SCENARIO
        scenario_steps = scenario["steps"]

        email = scenario_steps.get(1)
        step_two_task = scenario_steps.get(2)
        step_three_task = scenario_steps.get(3)
        step_four_task = scenario_steps.get(4)
        step_five_task = scenario_steps.get(5)

    elif (
        career_id == FRONTEND_SCENARIO["career_id"]
        and position_id == FRONTEND_SCENARIO["position_id"]
    ):
        scenario = FRONTEND_SCENARIO
        scenario_steps = scenario["steps"]

        email = scenario_steps.get(1)
        step_two_task = scenario_steps.get(2)
        step_three_task = scenario_steps.get(3)
        step_four_task = scenario_steps.get(4)
        step_five_task = scenario_steps.get(5)

    else:
        scenario = None

        email = (
            SIMULATION_DATA
            .get(career_id, {})
            .get(position_id)
        )

        step_two_task = (
            STEP_TWO_TASKS
            .get(career_id, {})
            .get(position_id)
        )

        step_three_task = (
            STEP_THREE_TASKS
            .get(career_id, {})
            .get(position_id)
        )

        step_four_task = (
            STEP_FOUR_TASKS
            .get(career_id, {})
            .get(position_id)
        )

        step_five_task = (
            STEP_FIVE_TASKS
            .get(career_id, {})
            .get(position_id)
        )

    # Return to the positions page if this simulation does not exist.
    if not email:
        return redirect(
            url_for(
                "positions",
                career_id=career_id
            )
        )

    # Identify the selected career, position, and company.
    simulation_key = (
        f"{career_id}|{position_id}|{company_id}"
    )

    # Check whether the user selected a different simulation.
    different_simulation = (
        session.get("simulation_key") != simulation_key
    )

    # reset=1 is added when the user clicks
    # "Practice for this role" from companies.html.
    restart_requested = (
        request.method == "GET"
        and step == 1
        and request.args.get("reset") == "1"
    )

    # Clear previous answers when starting a new attempt.
    if different_simulation or restart_requested:
        session["simulation_key"] = simulation_key
        session["simulation_answers"] = {}

        session.pop("scenario_id", None)
        session.pop("simulation_result", None)
        session.pop("simulation_result_id", None)
        session.pop("evaluation_result", None)
        session.pop("roadmap_result", None)

        # Remove the previous AI-generated attempt.
        # A new attempt will be generated after the redirect.
        session.pop("simulation_attempt_id", None)

    # Remove ?reset=1 from the address after clearing the attempt.
    if restart_requested:
        return redirect(
            url_for(
                "simulation_step",
                career_id=career_id,
                position_id=position_id,
                company_id=company_id,
                step=1
            )
        )

        # Remove ?reset=1 from the address after clearing the answers.
        if restart_requested:
            return redirect(
                url_for(
                    "simulation_step",
                    career_id=career_id,
                    position_id=position_id,
                    company_id=company_id,
                    step=1
                )
            )
        # The new AI-generated inbox is currently used only
    # for the Backend Developer position.
    is_backend_simulation = (
        career_id == BACKEND_SCENARIO["career_id"]
        and position_id == BACKEND_SCENARIO["position_id"]
    )

    is_frontend_simulation = (
        career_id == FRONTEND_SCENARIO["career_id"]
        and position_id == FRONTEND_SCENARIO["position_id"]
    )

    generated_inbox_task = None
    ai_generation_error = None

    if is_backend_simulation or is_frontend_simulation:
        user_id = session.get("user_id")

        if not user_id:
            return redirect(
                url_for("auth.login")
            )

        attempt_id = session.get("simulation_attempt_id")

        # First try to retrieve an already generated inbox.
        if attempt_id:
            generated_inbox_task = get_backend_inbox_task(
                user_id=user_id,
                attempt_id=attempt_id,
            )

        # Generate only when no saved inbox exists.
        if generated_inbox_task is None:
            try:
                if is_frontend_simulation:
                    complete_inbox_task = (
                        generate_frontend_inbox_task(
                            company_name=company_name
                        )
                    )

                    attempt_id = (
                        create_frontend_simulation_attempt(
                            user_id=user_id,
                            career_id=career_id,
                            position_id=position_id,
                            company_id=company_id,
                            generated_inbox_task=complete_inbox_task,
                        )
                    )
                else:
                    complete_inbox_task = generate_backend_inbox_task(
                        company_name=company_name
                    )

                    attempt_id = create_backend_simulation_attempt(
                        user_id=user_id,
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        generated_inbox_task=complete_inbox_task,
                    )

                # Store only the small Firebase ID in the Flask session.
                session["simulation_attempt_id"] = attempt_id

                # Read the public version back from Firebase.
                generated_inbox_task = get_backend_inbox_task(
                    user_id=user_id,
                    attempt_id=attempt_id,
                )

            except Exception:
                app.logger.exception(
                    "Gemini inbox generation or Firebase saving failed."
                )

                ai_generation_error = (
                    "We could not create the interactive inbox right now. "
                    "Please try starting the simulation again."
                )
        
    # These variables must exist for both GET and POST requests.
    error = None

    answers = session.get(
        "simulation_answers",
        {}
    )

    # Restore an earlier answer when the user presses Previous Step.
    saved_answer = answers.get(
        f"step_{step}",
        ""
    )

    # This section runs only when the form is submitted.
    if request.method == "POST":
        answer = request.form.get(
            "answer",
            ""
        ).strip()

        # Keep the submitted value available if validation fails.
        saved_answer = answer

        if not answer:
            error = "Please complete the task before continuing."

        # The interactive Backend inbox submits structured JSON.
        elif (
            is_backend_simulation or is_frontend_simulation
        ) and step == 1:
            try:
                validated_response = validate_inbox_response(
                    raw_answer=answer,
                    generated_task=generated_inbox_task,
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=1,
                    response=validated_response,
                )

            except InboxResponseValidationError as validation_error:
                app.logger.warning(
                    "Inbox response validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save Backend inbox response."
                )

                error = (
                    "We could not save your inbox response right now. "
                    "Please try again."
                )

            if not error:
                # Keep a session copy so Previous Step still works.
                answers["step_1"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=2,
                    )
                )
            
                    # The Backend incident investigation submits structured JSON.
        elif is_backend_simulation and step == 2:
            try:
                validated_response = (
                    validate_incident_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=2,
                    response=validated_response,
                )

            except (
                IncidentResponseValidationError
            ) as validation_error:
                app.logger.warning(
                    "Incident response validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save incident response."
                )

                error = (
                    "We could not save your investigation "
                    "right now. Please try again."
                )

            if not error:
                answers["step_2"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,    
                        company_id=company_id,
                        step=3,
                    )
                )

                # Backend Step 4 submits structured API test results.
        elif is_backend_simulation and step == 4:
            try:
                validated_response = (
                    validate_api_testing_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=4,
                    response=validated_response,
                )

            except (
                ApiTestingResponseValidationError
            ) as validation_error:
                app.logger.warning(
                    "API testing validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save API testing response."
                )

                error = (
                    "We could not save your API test results "
                    "right now. Please try again."
                )

            if not error:
                answers["step_4"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=5,
                    )
                )
                # Backend Step 5 submits a structured team-chat update.
        elif is_backend_simulation and step == 5:
            try:
                validated_response = (
                    validate_team_chat_response(
                        raw_answer=answer,
                    )
                )

                # Save the validated Step 5 response.
                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=5,
                    response=validated_response,
                )

                # Store a session copy for Previous Step and evaluation.
                answers["step_5"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                prepared_answers = (
                    prepare_answers_for_evaluation(
                        answers
                    )
                )

                simulation_data = {
                    "career": {
                        "id": career_id,
                        "name": career_name,
                    },
                    "position": {
                        "id": position_id,
                        "title": position_title,
                    },
                    "company": {
                        "id": company_id,
                        "name": company_name,
                    },
                    "scenario": {
                        "id": BACKEND_SCENARIO[
                            "scenario_id"
                        ],
                        "title": BACKEND_SCENARIO[
                            "title"
                        ],
                    },
                    "tasks": {
                        "step_1": generated_inbox_task,
                        "step_2": step_two_task,
                        "step_3": step_three_task,
                        "step_4": step_four_task,
                        "step_5": step_five_task,
                    },
                    "answers": prepared_answers,
                }

                # Gemini evaluates all five simulation activities.
                evaluation = evaluate_simulation(
                    simulation_data
                )

                # Save the evaluation before generating the roadmap.
                save_simulation_evaluation(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    evaluation=evaluation,
                )

                roadmap = generate_personalized_roadmap(
                    evaluation=evaluation,
                    career_name=career_name,
                    position_title=position_title,
                    company_name=company_name,
                )

                save_simulation_roadmap(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    roadmap=roadmap,
                )

                session["scenario_id"] = (
                    BACKEND_SCENARIO["scenario_id"]
                )

                session["evaluation_result"] = evaluation
                session["roadmap_result"] = roadmap

                # Kept for compatibility with the current results route.
                session["simulation_result"] = evaluation

            except (
                TeamChatResponseValidationError
            ) as validation_error:
                app.logger.warning(
                    "Team-chat validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except (
                SimulationEvaluationError
            ) as evaluation_error:
                app.logger.exception(
                    "Gemini simulation evaluation failed."
                )

                error = str(evaluation_error)

            except (
                RoadmapGenerationError
            ) as roadmap_error:
                app.logger.exception(
                    "Personalized roadmap generation failed."
                )

                error = str(roadmap_error)

            except Exception:
                app.logger.exception(
                    "Failed to finish the simulation."
                )

                error = (
                    "We could not finish your simulation "
                    "right now. Please try again."
                )

            if not error:
                result = prepare_evaluation_for_results_page(
                    evaluation,
                    _step_skill_names(
                        position_id=position_id
                    ),
                )

                return render_template(
                    "roadmap.html",
                    answers=prepared_answers,
                    evaluation=evaluation,
                    result=result,
                    roadmap=roadmap,
                )
        elif is_frontend_simulation and step == 2:
            try:
                validated_response = (
                    validate_frontend_investigation_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=2,
                    response=validated_response,
                )

            except (
                FrontendInvestigationValidationError
            ) as validation_error:
                app.logger.warning(
                    "Frontend investigation validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save frontend investigation response."
                )

                error = (
                    "We could not save your investigation "
                    "right now. Please try again."
                )

            if not error:
                answers["step_2"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=3,
                    )
                )

        elif is_frontend_simulation and step == 3:
            try:
                validated_response = (
                    validate_frontend_code_lab_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=3,
                    response=validated_response,
                )

            except (
                FrontendCodeLabValidationError
            ) as validation_error:
                app.logger.warning(
                    "Frontend code lab validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save frontend code lab response."
                )

                error = (
                    "We could not save your code right now. "
                    "Please try again."
                )

            if not error:
                answers["step_3"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=4,
                    )
                )

        elif is_frontend_simulation and step == 4:
            try:
                validated_response = (
                    validate_frontend_browser_testing_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=4,
                    response=validated_response,
                )

            except (
                FrontendBrowserTestingValidationError
            ) as validation_error:
                app.logger.warning(
                    "Frontend browser testing validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except Exception:
                app.logger.exception(
                    "Failed to save frontend browser test results."
                )

                error = (
                    "We could not save your browser test results "
                    "right now. Please try again."
                )

            if not error:
                answers["step_4"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=5,
                    )
                )

        elif is_frontend_simulation and step == 5:
            try:
                validated_response = (
                    validate_frontend_team_chat_response(
                        raw_answer=answer,
                    )
                )

                save_simulation_step_response(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    step=5,
                    response=validated_response,
                )

                answers["step_5"] = json.dumps(
                    validated_response
                )

                session["simulation_answers"] = answers

                prepared_answers = (
                    prepare_answers_for_evaluation(
                        answers
                    )
                )

                simulation_data = {
                    "career": {
                        "id": career_id,
                        "name": career_name,
                    },
                    "position": {
                        "id": position_id,
                        "title": position_title,
                    },
                    "company": {
                        "id": company_id,
                        "name": company_name,
                    },
                    "scenario": {
                        "id": FRONTEND_SCENARIO[
                            "scenario_id"
                        ],
                        "title": FRONTEND_SCENARIO[
                            "title"
                        ],
                    },
                    "tasks": {
                        "step_1": generated_inbox_task,
                        "step_2": step_two_task,
                        "step_3": step_three_task,
                        "step_4": step_four_task,
                        "step_5": step_five_task,
                    },
                    "answers": prepared_answers,
                }

                evaluation = evaluate_simulation(
                    simulation_data
                )

                save_simulation_evaluation(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    evaluation=evaluation,
                )

                roadmap = generate_personalized_roadmap(
                    evaluation=evaluation,
                    career_name=career_name,
                    position_title=position_title,
                    company_name=company_name,
                )

                save_simulation_roadmap(
                    user_id=session.get("user_id"),
                    attempt_id=session.get(
                        "simulation_attempt_id"
                    ),
                    roadmap=roadmap,
                )

                session["scenario_id"] = (
                    FRONTEND_SCENARIO["scenario_id"]
                )

                session["evaluation_result"] = evaluation
                session["roadmap_result"] = roadmap
                session["simulation_result"] = evaluation

            except (
                FrontendTeamChatValidationError
            ) as validation_error:
                app.logger.warning(
                    "Frontend team-chat validation failed: %s",
                    validation_error,
                )

                error = str(validation_error)

            except (
                SimulationEvaluationError
            ) as evaluation_error:
                app.logger.exception(
                    "Gemini simulation evaluation failed."
                )

                error = str(evaluation_error)

            except (
                RoadmapGenerationError
            ) as roadmap_error:
                app.logger.exception(
                    "Personalized roadmap generation failed."
                )

                error = str(roadmap_error)

            except Exception:
                app.logger.exception(
                    "Failed to finish the simulation."
                )

                error = (
                    "We could not finish your simulation "
                    "right now. Please try again."
                )

            if not error:
                result = prepare_evaluation_for_results_page(
                       evaluation,
                    _step_skill_names(
                        position_id=position_id
                    ),
                )

                return render_template(
                    "roadmap.html",
                    answers=prepared_answers,
                    evaluation=evaluation,
                    result=result,
                    roadmap=roadmap,
                    from_dashboard=False,
                )    
        # Frontend simulation behavior.
        else:
            answers[f"step_{step}"] = answer
            session["simulation_answers"] = answers

            if step < total_steps:
                return redirect(
                    url_for(
                        "simulation_step",
                        career_id=career_id,
                        position_id=position_id,
                        company_id=company_id,
                        step=step + 1,
                    )
                )

            # All five steps are complete, so prepare the evaluation.
            simulation_data = {
                "career": {
                    "id": career_id,
                    "name": career_name,
                },
                "position": {
                    "id": position_id,
                    "title": position_title,
                },
                "company": {
                    "id": company_id,
                    "name": company_name,
                },
                "tasks": {
                    "step_1": email,
                    "step_2": step_two_task,
                    "step_3": step_three_task,
                    "step_4": step_four_task,
                    "step_5": step_five_task,
                },
                "answers": prepare_answers_for_evaluation(answers),
            }

            try:
                evaluation = evaluate_simulation(simulation_data)

                roadmap_result = generate_personalized_roadmap(
                    evaluation=evaluation,
                    career_name=career_name,
                    position_title=position_title,
                    company_name=company_name,
                )

                return redirect(url_for("roadmap"))

            except SimulationEvaluationError as evaluation_error:
                app.logger.exception(
                    "Gemini simulation evaluation failed."
                )
                error = str(evaluation_error)

            except RoadmapGenerationError as roadmap_error:
                app.logger.exception(
                    "Personalized roadmap generation failed."
                )
                error = str(roadmap_error)

            except Exception:
                app.logger.exception(
                    "Failed to finish the simulation."
                )
                error = (
                    "We could not finish your simulation right now. "
                    "Please try again."
                )


    # Display the current simulation step.
    return render_template(
        "simulation.html",
        career_id=career_id,
        position_id=position_id,
        company_id=company_id,
        career_name=career_name,
        company_name=company_name,
        position_data=position_data,
        position_title=position_title,
        step=step,
        total_steps=total_steps,
        scenario=scenario,
        email=email,
        step_two_task=step_two_task,
        step_three_task=step_three_task,
        step_four_task=step_four_task,
        step_five_task=step_five_task,
        error=error,
        saved_answer=saved_answer,
        generated_inbox_task=generated_inbox_task,
        ai_generation_error=ai_generation_error,
        is_backend_simulation=is_backend_simulation,
        is_frontend_simulation=is_frontend_simulation,
    )



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


def _lookup_company_name(career_id, position_id, company_id):
    """Return the readable company name."""

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    for company in position.get("companies", []):
        if company.get("id") == company_id:
            return company.get("name", company_id)

    if company_id:
        return company_id.replace("-", " ").title()

    return "Company"


def _status_from_score(score):
    """Convert the score into a status."""

    if score >= 80:
        return "Strong Match"

    if score >= 60:
        return "Developing Match"

    return "Needs Practice"


def _format_completed_date(completed_at):
    """Format the completion date."""

    if not completed_at:
        return "Unknown date"

    try:
        cleaned = completed_at.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)

        # %#d is used on Windows.
        return parsed.strftime("%B %#d, %Y")

    except (ValueError, TypeError):
        return completed_at


def _build_dashboard_item(summary):
    """Prepare one simulation attempt for the dashboard."""

    career_id = summary.get("career_id")
    position_id = summary.get("position_id")
    company_id = summary.get("company_id")
    score = summary.get("overall_score", 0) or 0

    return {
        "attempt_id": summary.get("attempt_id"),
        "position_title": _lookup_position_title(
            career_id,
            position_id,
        ),
        "company_name": _lookup_company_name(
            career_id,
            position_id,
            company_id,
        ),
        "completed_date": _format_completed_date(
            summary.get("completed_at")
        ),
        "score": score,
        "status": _status_from_score(score),
    }


# =========================================================
# DASHBOARD ROUTES
# =========================================================

@app.route("/dashboard")
def dashboard():
    """Show the user's completed simulations."""

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    summaries = list_completed_simulation_attempts(user_id)

    attempts = [
        _build_dashboard_item(summary)
        for summary in summaries
    ]

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        attempts=attempts,
    )


@app.route("/dashboard/<attempt_id>")
def dashboard_attempt(attempt_id):
    """Open one completed simulation result."""

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    attempt = get_simulation_attempt(
        user_id=user_id,
        attempt_id=attempt_id,
    )

    if not attempt or attempt.get("status") != "completed":
        return redirect(url_for("dashboard"))

    evaluation = attempt.get("evaluation")
    roadmap = attempt.get("roadmap")

    result = prepare_evaluation_for_results_page(
        evaluation,
        _step_skill_names(
            position_id=attempt.get("position_id")
        ),
    )

    return render_template(
        "roadmap.html",
        answers=attempt.get("responses", {}),
        evaluation=evaluation,
        result=result,
        roadmap=roadmap,
        from_dashboard=True,
    )
# =========================================================
# ROADMAP ROUTE
# =========================================================

@app.route("/roadmap")
def roadmap():
    evaluation = session.get(
        "evaluation_result"
    )

    result = prepare_evaluation_for_results_page(
        evaluation,
        _step_skill_names(
            scenario_id=session.get("scenario_id")
        ),
    )

    return render_template(
        "roadmap.html",
        answers=session.get(
            "simulation_answers",
            {},
        ),
        evaluation=evaluation,
        result=result,
        roadmap=session.get("roadmap_result"),
    )


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)