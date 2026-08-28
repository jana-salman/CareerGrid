"""Register CareerGrid route Blueprints."""

from flask import Flask

from routes.api import api_bp
from routes.auth import auth_bp
from routes.careers import careers_bp
from routes.dashboard import dashboard_bp
from routes.frontend import frontend_bp
from routes.interviews import interviews_bp
from routes.simulations import simulations_bp


def register_blueprints(app: Flask) -> None:
    """Attach all route groups to a CareerGrid application."""

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(simulations_bp)
    app.register_blueprint(interviews_bp)
    # Register the SPA catch-all last so explicit page, API, and action routes win.
    app.register_blueprint(frontend_bp)
