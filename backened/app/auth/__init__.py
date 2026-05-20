"""
Auth Module — backened/app/auth/

This package contains all authentication and authorization logic:
  - Supabase Auth integration (signup, login, logout)
  - JWT verification and decoding
  - FastAPI dependency injection for protected routes
  - Role-based access control (RBAC) preparation
  - Pydantic schemas for auth request/response validation

Usage:
    from app.auth import auth_router
    app.include_router(auth_router)
"""

from app.auth.auth_routes import router as auth_router

__all__ = ["auth_router"]
