"""Small browser-safe API endpoints shared by frontend clients."""

from flask import Blueprint, jsonify


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    """Confirm that the Flask API is reachable without exposing internals."""

    return jsonify({"service": "careergrid", "status": "ok"})
