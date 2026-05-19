# =============================================================
# provider_service.py — Data layer for providers.json
# Pure Python, NO LLM calls. Fast, deterministic filtering.
# =============================================================

import json
from pathlib import Path
from typing import Any
from app.config.settings import PROVIDERS_PATH, DEBUG

# ------------------------------------------------------------------
# Module-level cache — load JSON once on import, not on every request
# ------------------------------------------------------------------
_providers: list[dict[str, Any]] = []


def _load_providers() -> list[dict[str, Any]]:
    """Load providers.json from disk. Called once at module import."""
    path = Path(PROVIDERS_PATH)
    if not path.exists():
        print(f"Error: providers.json not found at: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if DEBUG:
        print(f"Loaded {len(data)} providers from {path.name}")
    return data


# Load immediately when the module is first imported
_providers = _load_providers()


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def get_all_providers() -> list[dict[str, Any]]:
    """Return the full provider list (read-only reference)."""
    return _providers


def get_all_services() -> list[str]:
    """Return unique service types in the dataset."""
    return sorted(set(p["service"].lower() for p in _providers))


def get_all_locations() -> list[str]:
    """Return unique location names in the dataset."""
    return sorted(set(p["location"].lower() for p in _providers))


def filter_providers(
    service: str | None = None,
    location: str | None = None,
) -> list[dict[str, Any]]:
    """
    Filter providers by service and/or location.

    Matching is case-insensitive and uses substring matching so that:
      - "DHA"      matches "DHA Phase 1", "DHA Phase 2", etc.
      - "AC"       matches "AC technician"
      - "clifton"  matches "Clifton"

    Returns all providers if both filters are None (fallback).
    """
    results = _providers

    # --- Service filter ---
    if service:
        service_lower = service.lower().strip()
        results = [
            p for p in results
            # provider service contains query OR query contains provider service
            if service_lower in p["service"].lower()
            or p["service"].lower() in service_lower
        ]
        if DEBUG:
            print(f"🔍 After service filter '{service}': {len(results)} providers")

    # --- Location filter ---
    if location:
        location_lower = location.lower().strip()
        results = [
            p for p in results
            if location_lower in p["location"].lower()
            or p["location"].lower() in location_lower
        ]
        if DEBUG:
            print(f"🔍 After location filter '{location}': {len(results)} providers")

    # --- Fallback: if nothing matched, return all available providers ---
    if not results:
        if DEBUG:
            print("Warning: No exact matches found — returning all available providers")
        results = [p for p in _providers if p.get("available", False)]

    return results
