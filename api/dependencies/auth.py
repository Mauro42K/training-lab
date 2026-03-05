from fastapi import Header, HTTPException, status

from api.core.config import get_settings
from api.core.security import is_valid_api_key


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-KEY")) -> None:
    expected_key = get_settings().training_lab_api_key
    if not is_valid_api_key(x_api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
