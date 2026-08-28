"""Authentication routes for registration, login, and logout."""

from flask import (
    Blueprint,
    jsonify,
    redirect,
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
from routes.frontend import serve_react_app


auth_bp = Blueprint("auth", __name__)

PUBLIC_ENDPOINTS = {
    "api.health",
    "auth.login_api",
    "auth.register_api",
    "careers.home",
    "frontend.vite_asset",
    "auth.login",
    "auth.register",
    "auth.logout",
    "static",
}


def _set_authenticated_session(user):
    """Store only the browser session identity used by CareerGrid."""

    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]


def _authenticate(email, password):
    """Return a user only when normalized credentials are valid."""

    normalized_email = normalize_email(email)
    if not normalized_email or not password:
        return None

    user = get_user_by_email(normalized_email)
    if user is None:
        return None

    stored_password_hash = user.get("password_hash", "")
    if not stored_password_hash or not check_password_hash(
        stored_password_hash,
        password,
    ):
        return None

    return user


@auth_bp.before_app_request
def protect_pages():
    """Redirect anonymous visitors away from private CareerGrid pages."""

    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if request.path.startswith("/api/") and (
        "user_id" not in session or "user_email" not in session
    ):
        return jsonify(
            {
                "authenticated": False,
                "error": "Authentication required.",
            }
        ), 401

    if request.endpoint == "dashboard.dashboard" and "user_id" not in session:
        return redirect(url_for("auth.login"))

    if "user_email" not in session:
        return redirect(url_for("careers.home"))


@auth_bp.get("/login")
def login():
    """Serve the React login presentation."""

    return serve_react_app()


@auth_bp.get("/register")
def register():
    """Serve the React registration presentation."""

    return serve_react_app()


@auth_bp.route("/logout")
def logout():
    """Clear the current user's login session."""

    session.clear()

    return redirect(url_for("careers.home"))


@auth_bp.post("/api/auth/login")
def login_api():
    """Authenticate React clients with the existing Flask session cookie."""

    payload = request.get_json(silent=True) or {}
    email = normalize_email(str(payload.get("email", "")))
    password = str(payload.get("password", ""))
    if not email or not password:
        return jsonify({"error": "Please enter your email and password."}), 400

    user = _authenticate(email, password)
    if user is None:
        return jsonify({"error": "Incorrect email or password."}), 401

    _set_authenticated_session(user)
    return jsonify(
        {
            "authenticated": True,
            "user": {
                "email": session["user_email"],
                "id": session["user_id"],
                "name": session["user_name"],
            },
        }
    )


@auth_bp.post("/api/auth/register")
def register_api():
    """Create a Firebase-backed user for the React registration form."""

    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name", "")).strip()
    email = normalize_email(str(payload.get("email", "")))
    password = str(payload.get("password", ""))
    if not full_name or not email or not password:
        return jsonify({"error": "Please complete all fields."}), 400

    if get_user_by_email(email) is not None:
        return jsonify({"error": "An account with this email already exists."}), 409

    try:
        create_user(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
        )
    except ValueError as exception:
        return jsonify({"error": str(exception)}), 409

    return jsonify({"created": True}), 201


@auth_bp.post("/api/auth/logout")
def logout_api():
    """Clear the current Flask session without requiring a page redirect."""

    session.clear()
    return jsonify({"authenticated": False})
