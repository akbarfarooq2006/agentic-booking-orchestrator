import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt

# Load secret and expiration from environment (fallback defaults for development)
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = "HS256"
# Token expires in 1 hour by default
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT for a given user.

    Args:
        user_id: Supabase Auth user UID.
        role: Role assigned to the user (e.g., "user", "provider", "admin").
        expires_delta: Optional custom expiration; defaults to JWT_EXPIRATION_MINUTES.
    Returns:
        A JWT string.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    to_encode: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT.

    Raises:
        jwt.ExpiredSignatureError: if token is expired.
        jwt.InvalidTokenError: for any other validation issue.
    Returns:
        Payload dictionary containing at least ``sub`` (user_id) and ``role``.
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload


def get_user_from_token(token: str) -> Dict[str, str]:
    """Convenient helper returning user_id and role from a token.
    """
    payload = decode_access_token(token)
    return {"user_id": payload.get("sub"), "role": payload.get("role")}
