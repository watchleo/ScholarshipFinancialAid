"""Shared authentication for every scholarship API resource."""

import hmac
import os
from typing import Annotated

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: Annotated[str | None, Security(api_key_header)]):
    expected = os.environ.get("SCHOLARSHIP_API_KEY", "school-demo-key")
    if not key or not hmac.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(
            status_code=401,
            detail="Send a valid API key in the X-API-Key header.",
            headers={"WWW-Authenticate": 'ApiKey realm="scholarship"'},
        )
