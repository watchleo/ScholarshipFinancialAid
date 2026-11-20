"""Small helpers shared by the blueprint modules."""

from flask import request

from utils.exceptions import BadRequestError


def get_json_body():
    """Parse the request body as JSON; raise a clean 400 when invalid."""
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequestError(
            "Request body must be valid JSON with header "
            "'Content-Type: application/json'.")
    return data
