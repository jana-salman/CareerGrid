from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

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

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/career")
def career():
    return render_template("career.html")

@app.route("/simulation/<career_id>")
def simulation(career_id):
    return redirect(url_for("simulation_step", career_id=career_id, step=1))

@app.route("/simulation/<career_id>/<int:step>")
def simulation_step(career_id, step):
    career_name = career_id.replace("-", " ").title()
    total_steps = 5
    email = SIMULATION_DATA.get(career_id)
    return render_template(
        "simulation.html",
        career_id=career_id,
        career_name=career_name,
        step=step,
        total_steps=total_steps,
        email=email
    )

@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")

if __name__ == "__main__":
    app.run(debug=True)