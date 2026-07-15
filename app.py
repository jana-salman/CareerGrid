from flask import Flask, render_template, redirect, url_for, session, request
import os
import json
import requests
from dotenv import load_dotenv

from routes.auth import auth_bp
from services.simulation_result_service import save_simulation_result

from services.simulation_generator import (
    generate_backend_inbox_task,
)

from services.inbox_response_service import (
    InboxResponseValidationError,
    validate_inbox_response,
)

from services.simulation_storage import (
    save_simulation_step_response,
    create_backend_simulation_attempt,
    get_backend_inbox_task,
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
# BACKEND SIMULATION ANALYSIS
# =========================================================

def analyze_backend_answers(answers):
    """
    Analyze the five Backend simulation answers.

    Each simulation step is worth 20 points,
    giving a maximum total score of 100.
    """

    evaluation = BACKEND_SCENARIO["evaluation"]

    total_score = 0
    step_results = []
    strengths = []
    skills_to_improve = []

    for step_number, criteria in evaluation.items():
        answer = str(
            answers.get(f"step_{step_number}", "")
        ).strip()

        skill = criteria["skill"]
        step_score = 0
        matched_keywords = []

        # Step 3 is a multiple-choice question.
        if "correct_answer" in criteria:
            if answer == criteria["correct_answer"]:
                step_score = 20

        # Steps 1, 2, 4, and 5 are evaluated using keywords.
        else:
            keywords = criteria.get("keywords", [])
            normalized_answer = answer.lower()

            matched_keywords = [
                keyword
                for keyword in keywords
                if keyword.lower() in normalized_answer
            ]

            if keywords:
                step_score = round(
                    len(matched_keywords) / len(keywords) * 20
                )

        total_score += step_score

        if step_score >= 14:
            strengths.append(skill)
        else:
            skills_to_improve.append(skill)

        step_results.append({
            "step": step_number,
            "skill": skill,
            "score": step_score,
            "maximum_score": 20,
            "matched_keywords": matched_keywords
        })

    if total_score >= 80:
        performance_level = "Strong"
    elif total_score >= 60:
        performance_level = "Developing"
    else:
        performance_level = "Needs Practice"
        
        return {
        "score": total_score,
        "maximum_score": 100,
        "performance_level": performance_level,
        "strengths": strengths,
        "skills_to_improve": skills_to_improve,
        "step_results": step_results
}
# =========================================================
# POSITION AND COMPANY DATA
# =========================================================

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

    else:
        # Keep the current frontend simulation working.
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

    generated_inbox_task = None
    ai_generation_error = None

    if is_backend_simulation:
        user_id = session.get("user_id")

        if not user_id:
            return redirect(
                url_for("login")
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
        elif is_backend_simulation and step == 1:
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

        # Existing behavior for Frontend and Backend Steps 2–5.
        else:
            answers[f"step_{step}"] = answer
            session["simulation_answers"] = answers

            # Move to the next simulation step.
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

            # Step 5 is the final step.
            if scenario == BACKEND_SCENARIO:
                simulation_result = analyze_backend_answers(
                    answers
                )

                result_id = save_simulation_result(
                    user_id=session.get("user_id"),
                    career_id=career_id,
                    position_id=position_id,
                    company_id=company_id,
                    scenario_id=(
                        BACKEND_SCENARIO["scenario_id"]
                    ),
                    answers=answers,
                    result=simulation_result,
                )

                session["scenario_id"] = (
                    BACKEND_SCENARIO["scenario_id"]
                )

                session["simulation_result"] = (
                    simulation_result
                )

                session["simulation_result_id"] = (
                    result_id
                )

            return redirect(
                url_for("roadmap")
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
    )




# =========================================================
# ROADMAP ROUTE
# =========================================================

@app.route("/roadmap")
def roadmap():
    return render_template(
        "roadmap.html",
        answers=session.get("simulation_answers", {}),
        result=session.get("simulation_result")
    )


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)