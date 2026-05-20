"""
Auth Middleware — Global request/response processing for authentication.

Provides two middleware components:
1. AuthMiddleware: Logs auth-related request info (development aid).
2. CORS configuration helper for mobile app access.

This middleware does NOT enforce authentication globally — that's handled
by the FastAPI dependencies (get_current_user, require_role) on a per-route
basis. This middleware handles cross-cutting concerns like CORS and logging.

Usage in main.py:
    from app.auth.middleware import add_auth_middleware
    add_auth_middleware(app)
"""

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("auth.middleware")


class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs authentication-related request details.

    In development, this helps trace auth flow issues by logging:
    - Whether an Authorization header is present
    - Request method and path
    - Response status code and timing

    In production, reduce log level or remove this middleware.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Check if request has auth header (don't log the actual token!)
        has_auth = "authorization" in request.headers
        auth_status = "authenticated" if has_auth else "anonymous"

        logger.debug(
            f"[{auth_status}] {request.method} {request.url.path}"
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"[{auth_status}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms:.1f}ms)"
        )

        return response


def add_auth_middleware(app: FastAPI) -> None:
    """
    Attach all auth-related middleware to the FastAPI application.

    Call this once in main.py during app startup.

    Configures:
    - CORS: Allows the React Native / Expo mobile app to call the API.
    - Auth Logging: Development-friendly request tracing.
    """

    # ---- CORS ----
    # React Native / Expo apps need CORS to communicate with the backend.
    # In production, restrict origins to your actual domain(s).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*",  # Allow all origins for hackathon/development
            # In production, replace with specific origins:
            # "https://your-app-domain.com",
            # "exp://192.168.x.x:8081",  # Expo Go local dev
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    # ---- Auth Logging ----
    app.add_middleware(AuthLoggingMiddleware)

    logger.info("Auth middleware stack configured.")
