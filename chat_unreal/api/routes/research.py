"""Research endpoint implementation."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from ...api.auth import verify_request
from ...api.utils import logging_utils, validators
from ...connectors.api_handler import get_handler

blueprint = Blueprint("research", __name__, url_prefix="/api/research")


@blueprint.post("/")
def research() -> Response:
    if not verify_request(request.headers.get("X-API-KEY")):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        validators.validate_endpoint("research")
        payload = validators.validate_payload(request.get_json(silent=True), required_fields=["query"])
    except validators.ValidationError as exc:
        return jsonify({"error": exc.message}), 400

    handler = get_handler()
    query = str(payload["query"]).strip()
    data = handler.research(query)
    logging_utils.log_api_call("research", payload)
    return jsonify(data)
