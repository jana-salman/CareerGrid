"""CareerGrid Flask application factory and development entrypoint."""

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import build_app_config, environment_flag, secret_key
from routes import register_blueprints


_environment_flag = environment_flag
_secret_key = secret_key


def create_app(config_overrides: dict | None = None) -> Flask:
    """Create and configure one CareerGrid Flask application."""

    application = Flask(__name__)
    application.config.from_mapping(build_app_config())

    if config_overrides:
        application.config.update(config_overrides)

    register_blueprints(application)

    limiter = Limiter(
        get_remote_address,
        app=application,
        default_limits=[],
        storage_uri="memory://",
    )
    application.view_functions["auth.login_api"] = limiter.limit("10 per minute")(
        application.view_functions["auth.login_api"]
    )
    application.view_functions["auth.register_api"] = limiter.limit("5 per minute")(
        application.view_functions["auth.register_api"]
    )

    @application.errorhandler(404)
    def api_not_found(error):
        """Keep unmatched API responses JSON-safe for browser clients."""

        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "error": (
                        "CareerGrid could not find the requested information. "
                        "Please refresh and try again."
                    )
                }
            ), 404

        return error

    @application.errorhandler(405)
    def api_method_not_allowed(error):
        """Keep unsupported API methods JSON-safe without affecting page routes."""

        if request.path.startswith("/api/"):
            return jsonify({"error": "Method not allowed."}), 405

        return error

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
