"""Market analysis endpoint."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from ...api.auth import verify_request
from ...api.utils import logging_utils, validators
from ...connectors.api_handler import get_handler

blueprint = Blueprint("market", __name__, url_prefix="/api/market")


@blueprint.post("/")
def market() -> Response:
    if not verify_request(request.headers.get("X-API-KEY")):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        validators.validate_endpoint("market")
        payload = validators.validate_payload(request.get_json(silent=True), required_fields=["topic"])
    except validators.ValidationError as exc:
        return jsonify({"error": exc.message}), 400

    handler = get_handler()
    topic = str(payload["topic"]).strip()
    data = handler.market_analysis(topic)
    logging_utils.log_api_call("market", payload)
    return jsonify(data)
