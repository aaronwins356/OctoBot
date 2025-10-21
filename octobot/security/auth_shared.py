import os
from fastapi import Header, HTTPException, status

OCTOBOT_KEY = os.getenv("OCTOBOT_KEY")

def verify_token(x_api_key: str = Header(None)):
    """Fail-closed header-based auth shared across OctoBot services."""
    if not OCTOBOT_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCTOBOT_KEY not configured on server."
        )
    if x_api_key != OCTOBOT_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )
    return x_api_key
