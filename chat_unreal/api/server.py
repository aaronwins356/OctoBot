"""Flask application entry point for Chat Unreal."""

from __future__ import annotations

from flask import Flask

from .routes import github, health, market, research


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(health.blueprint)
    app.register_blueprint(research.blueprint)
    app.register_blueprint(market.blueprint)
    app.register_blueprint(github.blueprint)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)
