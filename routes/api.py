"""Small browser-safe API endpoints shared by frontend clients."""

from flask import Blueprint, jsonify, session


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    """Confirm that the Flask API is reachable without exposing internals."""

    return jsonify({"service": "careergrid", "status": "ok"})


@api_bp.get("/auth/session")
def session_status():
    """Return the signed-in user's browser-safe session identity."""

    return jsonify(
        {
            "authenticated": True,
            "user": {
                "email": session["user_email"],
                "id": session["user_id"],
                "name": session.get("user_name", ""),
            },
        }
    )
