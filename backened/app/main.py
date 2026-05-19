# =============================================================
# main.py — FastAPI application entry point
#
# Wires up the app, CORS middleware, and routers.
# Run with: uv run uvicorn app.main:app --reload --port 8000
# =============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.config.settings import APP_NAME, DEBUG

# ------------------------------------------------------------------
# App instance
# ------------------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    description="Multi-agent AI workflow system for home services booking in Karachi.",
    version="0.1.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",
)

# ------------------------------------------------------------------
# CORS — allow Flutter app and web clients to connect
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])


# ------------------------------------------------------------------
# Health check endpoint
# ------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    """Quick health check — confirms the server is running."""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
    }


# ------------------------------------------------------------------
# Startup event — useful for pre-loading data / checking config
# ------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Runs once when the server starts."""
    print(f"\n{APP_NAME} is starting up...")
    if DEBUG:
        print("DEBUG mode is ON — verbose agent logs will appear")

    # Trigger provider data load by importing the service
    # (module-level cache loads providers.json on first import)
    from app.services.provider_service import get_all_providers
    providers = get_all_providers()
    print(f"Loaded {len(providers)} providers from mock dataset")
    print(f"API ready -> http://localhost:8000/docs\n")
