import json
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash


auth_bp = Blueprint("auth", __name__)

# CareerGrid/data/users.json
USERS_FILE = Path(__file__).resolve().parent.parent / "data" / "users.json"


def load_users():
    """Read and return all registered users."""
    try:
        with USERS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_users(users):
    """Save the updated users list."""
    USERS_FILE.parent.mkdir(exist_ok=True)

    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    message = None

    if request.args.get("registered") == "1":
        message = "Account created successfully. Please log in."

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Please enter your email and password."
            return render_template(
                "login.html",
                error=error,
                message=message
            )

        users = load_users()

        user = next(
            (
                user
                for user in users
                if user.get("email", "").lower() == email
            ),
            None
        )

        if user is None or not check_password_hash(
            user.get("password", ""),
            password
        ):
            error = "Incorrect email or password."
            return render_template(
                "login.html",
                error=error,
                message=message
            )

        session["user_email"] = user["email"]
        session["user_name"] = user["full_name"]

        return redirect(url_for("career"))

    return render_template(
        "login.html",
        error=error,
        message=message
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            error = "Please complete all fields."
            return render_template("register.html", error=error)

        users = load_users()

        email_already_exists = any(
            user.get("email", "").lower() == email
            for user in users
        )

        if email_already_exists:
            error = "An account with this email already exists."
            return render_template("register.html", error=error)

        new_user = {
            "full_name": full_name,
            "email": email,
            "password": generate_password_hash(password)
        }

        users.append(new_user)
        save_users(users)

        return redirect(url_for("auth.login", registered="1"))

    return render_template("register.html", error=error)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))