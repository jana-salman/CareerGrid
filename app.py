from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

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
    return render_template(
        "simulation.html",
        career_id=career_id,
        career_name=career_name,
        step=step,
        total_steps=total_steps
    )
@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")

if __name__ == "__main__":
    app.run(debug=True)
    
    
