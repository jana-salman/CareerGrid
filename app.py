from flask import Flask, render_template, redirect, url_for, session
import requests
import os
from dotenv import load_dotenv
from routes.auth import auth_bp

load_dotenv()

app = Flask(__name__)
#Flask needs this key to store login information safely inside the session.
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "careergrid-development-key"
)
app.register_blueprint(auth_bp)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

SIMULATION_DATA = {
    "software-developer": {
        "sender": "Alex Carter, Team Lead",
        "subject": "Bug reported in checkout page",
        "body": "Hey, a customer reported that clicking 'Buy Now' sometimes does nothing. "
                "Can you take a look today? I've attached the error log below. "
                "We need this fixed before end of day — it's affecting sales."
    },
    "ui-ux-designer": {
        "sender": "Priya Shah, Product Manager",
        "subject": "Users dropping off the signup form",
        "body": "Our signup completion rate dropped 20% this month. "
                "Can you review the form and tell me what might be causing friction? "
                "I'd like your thoughts before our next design review."
    },
    "data-analyst": {
        "sender": "Sam Reyes, Marketing Lead",
        "subject": "Need insight before Monday's meeting",
        "body": "Can you pull last month's campaign numbers and tell me which channel "
                "performed best? I need to present this to leadership on Monday."
    }
}

POSITIONS_DATA = {
    "software-developer": {
        "backend-developer": {
            "title": "Backend Developer",
            "companies": [
                {"id": "technova", "name": "TechNova", "location": "Local"},
                {"id": "brightsoft", "name": "BrightSoft", "location": "Global"}
            ]
        },
        "frontend-developer": {
            "title": "Frontend Developer",
            "companies": [
                {"id": "pixelworks", "name": "PixelWorks", "location": "Local"},
                {"id": "cloudbyte", "name": "CloudByte", "location": "Global"}
            ]
        }
    }
}
def fetch_adzuna_jobs(job_title, location="", results=5):
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
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print("Adzuna API error:", e)
        return []

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/career")
def career():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "career.html",
        user_name=session.get("user_name")
    )

@app.route("/positions/<career_id>")
def positions(career_id):
    career_name = career_id.replace("-", " ").title()
    position_data = POSITIONS_DATA.get(career_id, {})
    return render_template(
        "positions.html",
        career_id=career_id,
        career_name=career_name,
        positions=position_data
    )

@app.route("/positions/<career_id>/<position_id>")
def companies(career_id, position_id):
    career_name = career_id.replace("-", " ").title()
    position_data = POSITIONS_DATA.get(career_id, {}).get(position_id, {})
    position_title = position_data.get("title", "")

    jobs = fetch_adzuna_jobs(position_title)

    return render_template(
        "companies.html",
        career_id=career_id,
        career_name=career_name,
        position_id=position_id,
        position_title=position_title,
        jobs=jobs
    )

@app.route("/simulation/<career_id>/<position_id>/<company_id>/<int:step>")
def simulation_step(career_id, position_id, company_id, step):
    career_name = career_id.replace("-", " ").title()
    total_steps = 5
    email = SIMULATION_DATA.get(career_id)

    position_data = POSITIONS_DATA.get(career_id, {}).get(position_id, {})
    position_title = position_data.get("title", "")

    company_name = company_id.replace("-", " ")

    return render_template(
        "simulation.html",
        career_id=career_id,
        career_name=career_name,
        position_id=position_id,
        position_title=position_title,
        company_id=company_id,
        company_name=company_name,
        step=step,
        total_steps=total_steps,
        email=email
    )

@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")

if __name__ == "__main__":
    app.run(debug=True)