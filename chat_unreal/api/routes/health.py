"""Health endpoint."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify

from ... import __version__

blueprint = Blueprint("health", __name__, url_prefix="/api/health")


@blueprint.get("/")
def health() -> Response:
    return jsonify({"status": "ok", "version": __version__})
