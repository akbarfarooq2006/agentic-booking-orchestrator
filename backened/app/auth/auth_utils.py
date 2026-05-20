"""
Auth Utilities — Shared helper functions for the auth module.

Contains utility functions used across auth routes, middleware, and
dependencies. Kept separate to avoid circular imports and improve testability.

Usage:
    from app.auth.auth_utils import extract_bearer_token, safe_user_dict
"""

import re
from typing import Optional, Dict, Any


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract the token from a 'Bearer <token>' authorization header.

    Args:
        authorization_header: The raw Authorization header value.

    Returns:
        The token string, or None if the header is missing/malformed.

    Example:
        >>> extract_bearer_token("Bearer eyJhbGciOiJI...")
        'eyJhbGciOiJI...'
        >>> extract_bearer_token(None)
        None
    """
    if not authorization_header:
        return None

    match = re.match(r"^Bearer\s+(.+)$", authorization_header, re.IGNORECASE)
    return match.group(1) if match else None


def safe_user_dict(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a user data dictionary for safe logging/response.

    Removes sensitive fields like password hashes, tokens, and secrets.
    Use this before logging user objects or returning them in error responses.

    Args:
        user_data: Raw user dictionary (e.g., from Supabase).

    Returns:
        A copy of the dictionary with sensitive fields removed.
    """
    sensitive_keys = {
        "password", "password_hash", "hashed_password",
        "access_token", "refresh_token", "token",
        "secret", "api_key", "service_role_key",
    }

    return {
        key: value
        for key, value in user_data.items()
        if key.lower() not in sensitive_keys
    }


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and return validation results.

    This is a lightweight check for hackathon use. In production,
    Supabase handles password policy enforcement server-side.

    Args:
        password: The password string to validate.

    Returns:
        Dictionary with 'valid' (bool) and 'errors' (list of strings).
    """
    errors = []

    if len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if len(password) > 72:
        errors.append("Password must be no longer than 72 characters.")
    if not re.search(r"[A-Za-z]", password):
        errors.append("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def format_supabase_error(error: Exception) -> str:
    """
    Extract a user-friendly message from a Supabase exception.

    Supabase exceptions often contain nested JSON messages; this function
    tries to extract the meaningful part.
    """
    error_str = str(error)

    # Common Supabase error patterns
    known_messages = {
        "User already registered": "An account with this email already exists.",
        "Invalid login credentials": "Invalid email or password.",
        "Email not confirmed": "Please confirm your email before logging in.",
        "Password should be at least": "Password is too short (minimum 6 characters).",
    }

    for pattern, friendly_msg in known_messages.items():
        if pattern.lower() in error_str.lower():
            return friendly_msg

    return f"Authentication error: {error_str}"
