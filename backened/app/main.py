"""
FastAPI Application Entry Point.

Initializes the FastAPI app, registers routers, and attaches middleware.
This file is owned by the auth branch but designed to be merge-friendly:
  - Teammates add their own routers via `app.include_router(...)`.
  - The auth middleware stack is isolated in app.auth.middleware.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.auth import auth_router
from app.auth.middleware import add_auth_middleware

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("app")


# ---------------------------------------------------------------------------
# Application Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.

    Startup:
      - Logs configuration status.
      - Future: Initialize DB connection pools, warm caches, etc.

    Shutdown:
      - Future: Close DB connections, flush logs, etc.
    """
    logger.info("🚀 Starting Agentic Booking Orchestrator API...")
    logger.info("✅ Auth module loaded.")
    yield
    logger.info("👋 Shutting down...")


# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agentic Booking Orchestrator API",
    description=(
        "AI-powered service booking platform for the informal economy. "
        "Handles user authentication, provider matching, and booking orchestration."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# ---- Middleware ----
add_auth_middleware(app)

# ---- Routers ----
# Auth routes: /auth/signup, /auth/login, /auth/logout, /auth/me
app.include_router(auth_router)

# Future: Teammate routers will be added here:
# from app.routes.booking import booking_router
# app.include_router(booking_router, prefix="/api/v1")
# from app.routes.agents import agent_router
# app.include_router(agent_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint for deployment verification."""
    return {"status": "healthy", "service": "agentic-booking-orchestrator"}
