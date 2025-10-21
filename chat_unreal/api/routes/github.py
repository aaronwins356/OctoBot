"""GitHub integration endpoint."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from ...api.auth import verify_request
from ...api.utils import logging_utils, validators
from ...connectors.api_handler import get_handler

blueprint = Blueprint("github", __name__, url_prefix="/api/github")


@blueprint.post("/")
def github_search() -> Response:
    if not verify_request(request.headers.get("X-API-KEY")):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        validators.validate_endpoint("github")
        payload = validators.validate_payload(request.get_json(silent=True), required_fields=["keyword"])
    except validators.ValidationError as exc:
        return jsonify({"error": exc.message}), 400

    handler = get_handler()
    keyword = str(payload["keyword"]).strip()
    data = handler.github_trending(keyword)
    logging_utils.log_api_call("github", payload)
    return jsonify(data)
