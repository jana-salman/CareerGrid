from flask import Flask, render_template

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

@app.route("/simulation")
def simulation():
    return render_template("simulation.html")

@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")

if __name__ == "__main__":
    app.run(debug=True)
    