"""Register CareerGrid route Blueprints."""

from flask import Flask

from routes.auth import auth_bp
from routes.careers import careers_bp
from routes.dashboard import dashboard_bp
from routes.interviews import interviews_bp
from routes.simulations import simulations_bp


def register_blueprints(app: Flask) -> None:
    """Attach all route groups to a CareerGrid application."""

    app.register_blueprint(auth_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(simulations_bp)
    app.register_blueprint(interviews_bp)
