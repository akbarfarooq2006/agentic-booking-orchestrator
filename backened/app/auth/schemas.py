"""
Auth Schemas — Pydantic models for request/response validation.

These models define the exact shape of data flowing through the auth endpoints.
FastAPI uses them automatically for request parsing, response serialization,
and OpenAPI documentation.

Usage:
    from app.auth.schemas import SignupRequest, LoginRequest, AuthResponse
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.auth.roles import UserRole


# =============================================================================
# Request Models
# =============================================================================

class SignupRequest(BaseModel):
    """Body for POST /auth/signup"""
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(
        ...,
        min_length=6,
        description="Password (min 6 characters)",
        examples=["securePassword123"],
    )
    # Role defaults to "user"; can be set to "provider" during provider signup
    role: UserRole = Field(
        default=UserRole.USER,
        description="Role to assign (user, provider, admin)",
    )


class LoginRequest(BaseModel):
    """Body for POST /auth/login"""
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["securePassword123"])


# =============================================================================
# Response Models
# =============================================================================

class UserProfile(BaseModel):
    """Public user profile returned by GET /auth/me and embedded in AuthResponse."""
    id: str = Field(..., description="Supabase user UID")
    email: str = Field(..., description="User email")
    role: str = Field(default="user", description="User role")
    created_at: Optional[str] = Field(None, description="ISO timestamp of account creation")


class AuthResponse(BaseModel):
    """Successful auth response (signup/login).

    Contains tokens for the mobile client to store securely and a user profile.
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token for session renewal")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: Optional[int] = Field(None, description="Token TTL in seconds")
    user: UserProfile


class MessageResponse(BaseModel):
    """Generic message response (e.g., logout confirmation)."""
    message: str = Field(..., description="Human-readable status message")
    success: bool = Field(default=True)


class ErrorResponse(BaseModel):
    """Standardized error response."""
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
