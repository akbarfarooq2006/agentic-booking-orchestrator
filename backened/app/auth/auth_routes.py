"""
Auth Routes — POST /auth/signup, POST /auth/login, POST /auth/logout, GET /auth/me

Handles all authentication endpoints using Supabase Auth as the identity provider.
When Supabase is not configured (no env vars), falls back to mock mode for
local development and hackathon demos.

All endpoints are prefixed with /auth (set in the router).

Usage:
    from app.auth import auth_router
    app.include_router(auth_router)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.schemas import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserProfile,
    MessageResponse,
    ErrorResponse,
)
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.auth.roles import UserRole
from app.auth.config import auth_settings

# ---------------------------------------------------------------------------
# Router Setup
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
    },
)


# ---------------------------------------------------------------------------
# Helper: Determine if Supabase is available
# ---------------------------------------------------------------------------

def _supabase_configured() -> bool:
    """Check whether Supabase credentials are present in the environment."""
    return bool(auth_settings.SUPABASE_URL and auth_settings.SUPABASE_ANON_KEY)


def _get_supabase():
    """Lazy-import the Supabase client to avoid import errors when not configured."""
    if not _supabase_configured():
        return None
    from app.auth.supabase_client import supabase
    return supabase


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------

@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    responses={400: {"model": ErrorResponse}},
)
async def signup(request: SignupRequest):
    """
    Register a new user via Supabase Auth.

    **Flow:**
    1. Sends email/password to Supabase `auth.sign_up()`.
    2. Supabase creates the user and returns a session.
    3. We mint our own JWT containing the user's role for RBAC.
    4. Returns access token + user profile to the mobile client.

    **Mock mode:** When Supabase is not configured, generates a mock user
    so the frontend team can develop without waiting for real Supabase setup.
    """
    sb = _get_supabase()

    if sb:
        # ---- Real Supabase signup ----
        try:
            response = sb.auth.sign_up({
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "role": request.role.value,  # Store role in user_metadata
                    }
                }
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup failed: {str(e)}",
            )

        # Supabase returns user + session
        user = response.user
        session = response.session

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed: Supabase did not return a user.",
            )

        user_id = user.id
        email = user.email or request.email
        role = request.role.value
        created_at = (
            user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None
        )

        # Mint a custom JWT with role embedded (Supabase tokens don't carry our role)
        access_token = create_access_token(user_id=str(user_id), role=role)
        refresh_token = session.refresh_token if session else None

    else:
        # ---- Mock mode (no Supabase) ----
        user_id = str(uuid.uuid4())
        email = request.email
        role = request.role.value
        created_at = datetime.utcnow().isoformat()
        access_token = create_access_token(user_id=user_id, role=role)
        refresh_token = f"mock_refresh_{uuid.uuid4().hex[:16]}"

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserProfile(
            id=str(user_id),
            email=email,
            role=role,
            created_at=created_at,
        ),
    )


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email and password",
    responses={401: {"model": ErrorResponse}},
)
async def login(request: LoginRequest):
    """
    Authenticate an existing user via Supabase Auth.

    **Flow:**
    1. Sends email/password to Supabase `auth.sign_in_with_password()`.
    2. Supabase verifies credentials and returns a session.
    3. We extract the role from user_metadata and mint our own RBAC JWT.
    4. Returns access token + user profile to the mobile client.

    **Mock mode:** Accepts any email/password and returns a mock session.
    """
    sb = _get_supabase()

    if sb:
        # ---- Real Supabase login ----
        try:
            response = sb.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password,
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}",
            )

        user = response.user
        session = response.session

        if not user or not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        user_id = user.id
        email = user.email or request.email
        # Retrieve role from Supabase user_metadata (set during signup)
        role = (user.user_metadata or {}).get("role", UserRole.USER.value)
        created_at = (
            user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None
        )

        access_token = create_access_token(user_id=str(user_id), role=role)
        refresh_token = session.refresh_token

    else:
        # ---- Mock mode ----
        user_id = str(uuid.uuid4())
        email = request.email
        role = UserRole.USER.value
        created_at = datetime.utcnow().isoformat()
        access_token = create_access_token(user_id=user_id, role=role)
        refresh_token = f"mock_refresh_{uuid.uuid4().hex[:16]}"

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserProfile(
            id=str(user_id),
            email=email,
            role=role,
            created_at=created_at,
        ),
    )


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out the current user",
)
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Invalidate the current session.

    **Flow:**
    1. Validates the JWT via `get_current_user` dependency.
    2. Calls Supabase `auth.sign_out()` to revoke the server-side session.
    3. Returns success — the mobile client should delete stored tokens.

    **Note:** JWT is stateless; actual invalidation requires the client
    to discard the token. Supabase sign_out revokes the refresh token.
    """
    sb = _get_supabase()

    if sb:
        try:
            sb.auth.sign_out()
        except Exception:
            # Even if Supabase sign_out fails, we tell the client to clear tokens
            pass

    return MessageResponse(
        message=f"User {current_user.email} logged out successfully.",
        success=True,
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get the current authenticated user's profile",
)
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Return the profile of the currently authenticated user.

    **Usage:** The mobile client calls this on app startup to verify
    that a stored token is still valid and to hydrate the user state.

    The `get_current_user` dependency handles JWT verification automatically.
    If the token is invalid/expired, a 401 is returned before this function runs.
    """
    return current_user
