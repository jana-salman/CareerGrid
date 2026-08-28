"""CareerGrid Flask application factory and development entrypoint."""

from flask import Flask, jsonify, request

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
