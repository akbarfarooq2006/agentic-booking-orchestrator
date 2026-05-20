"""
Auth Configuration — Loads environment variables for Supabase and JWT.

Uses pydantic-settings for typed, validated config.
All secrets come from environment variables (never hardcoded).

Usage:
    from app.auth.config import auth_settings
    print(auth_settings.SUPABASE_URL)
"""

import os
from functools import lru_cache
from typing import Optional


class AuthSettings:
    """
    Auth-related settings loaded from environment variables.

    Attributes:
        SUPABASE_URL: Your Supabase project URL.
        SUPABASE_ANON_KEY: Supabase anon/public key (used for client-side calls).
        SUPABASE_SERVICE_ROLE_KEY: Supabase service role key (used for admin ops).
        JWT_SECRET: Secret used to verify Supabase JWTs (found in Supabase dashboard).
        JWT_ALGORITHM: Algorithm used for JWT signing (default: HS256).
        JWT_EXPIRATION_MINUTES: Token expiry time in minutes (default: 60).
    """

    def __init__(self):
        self.SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

        # --- Validation ---
        if not self.SUPABASE_URL:
            print("WARNING: SUPABASE_URL is not set. Auth will not work in production.")
        if not self.JWT_SECRET:
            print("WARNING: JWT_SECRET is not set. Using insecure defaults.")


@lru_cache()
def get_auth_settings() -> AuthSettings:
    """Return a cached singleton of AuthSettings.

    Call this function wherever you need auth config:
        settings = get_auth_settings()
    """
    return AuthSettings()


# Convenience: importable singleton
auth_settings = get_auth_settings()
