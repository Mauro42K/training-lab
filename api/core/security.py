import secrets


def is_valid_api_key(provided_key: str | None, expected_key: str | None) -> bool:
    if not provided_key or not expected_key:
        return False
    return secrets.compare_digest(provided_key, expected_key)
