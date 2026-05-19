# =============================================================
# settings.py — App configuration loaded from .env
# =============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (backened/.env)
# Path: backened/app/config/settings.py → go up 3 levels to reach backened/
_ROOT = Path(__file__).resolve().parents[2]  # → backened/
load_dotenv(_ROOT / ".env", override=True)

# ------------------------------------------------------------------
# Gemini API settings (OpenAI-compatible endpoint)
# ------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE_URL: str = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ------------------------------------------------------------------
# App settings
# ------------------------------------------------------------------
APP_NAME: str = os.getenv("APP_NAME", "Agentic Booking Orchestrator")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ------------------------------------------------------------------
# Mock data path — providers.json lives at backened/app/mock/
# ------------------------------------------------------------------
PROVIDERS_PATH: Path = _ROOT / "app" / "mock" / "providers.json"

# ------------------------------------------------------------------
# Validate at startup (helpful for debugging)
# ------------------------------------------------------------------
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set in .env!")

if DEBUG:
    print(f"Settings loaded | Model: {GEMINI_MODEL} | Providers: {PROVIDERS_PATH}")
