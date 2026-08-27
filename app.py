"""CareerGrid Flask application factory and development entrypoint."""

from flask import Flask

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
    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
