from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from services.user_service import (
    create_user,
    get_user_by_email,
    normalize_email,
)


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Log an existing CareerGrid user into the website."""

    error = None
    message = None

    if request.args.get("registered") == "1":
        message = (
            "Account created successfully. Please log in."
        )

    if request.method == "POST":
        email = normalize_email(
            request.form.get("email", "")
        )
        password = request.form.get("password", "")

        if not email or not password:
            error = "Please enter your email and password."

            return render_template(
                "login.html",
                error=error,
                message=message
            )

        user = get_user_by_email(email)

        if user is None:
            error = "Incorrect email or password."

            return render_template(
                "login.html",
                error=error,
                message=message
            )

        stored_password_hash = user.get(
            "password_hash",
            ""
        )

        if (
            not stored_password_hash
            or not check_password_hash(
                stored_password_hash,
                password
            )
        ):
            error = "Incorrect email or password."

            return render_template(
                "login.html",
                error=error,
                message=message
            )

        # Save only the information needed for the login session.
        session["user_id"] = user["id"]
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
    """Register a new CareerGrid user."""

    error = None

    if request.method == "POST":
        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = normalize_email(
            request.form.get("email", "")
        )

        password = request.form.get("password", "")

        if not full_name or not email or not password:
            error = "Please complete all fields."

            return render_template(
                "register.html",
                error=error
            )

        existing_user = get_user_by_email(email)

        if existing_user is not None:
            error = (
                "An account with this email already exists."
            )

            return render_template(
                "register.html",
                error=error
            )

        password_hash = generate_password_hash(
            password
        )

        try:
            create_user(
                full_name=full_name,
                email=email,
                password_hash=password_hash
            )
        except ValueError as exception:
            return render_template(
                "register.html",
                error=str(exception)
            )

        return redirect(
            url_for(
                "auth.login",
                registered="1"
            )
        )

    return render_template(
        "register.html",
        error=error
    )


@auth_bp.route("/logout")
def logout():
    """Clear the current user's login session."""

    session.clear()

    return redirect(url_for("home"))