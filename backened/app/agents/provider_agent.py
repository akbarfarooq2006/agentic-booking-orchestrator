# =============================================================
# provider_agent.py — Search providers.json for matching providers
#
# Pure Python — NO LLM calls. Delegates to provider_service.py.
# Fast and deterministic. Returns a filtered list of providers.
# =============================================================

from typing import Any
from app.services.provider_service import filter_providers
from app.config.settings import DEBUG


async def run_provider_agent(
    service: str | None,
    location: str | None,
) -> list[dict[str, Any]]:
    """
    Search the mock providers dataset for matching providers.

    This agent is intentionally simple — it wraps the provider_service
    filter function and adds debug logging.

    Args:
        service:  Service type from intent (e.g. "plumber", "AC technician")
        location: Area name from intent (e.g. "DHA", "Clifton")

    Returns:
        List of matching provider dicts from providers.json
    """
    if DEBUG:
        print(f"[ProviderAgent] Searching: service='{service}', location='{location}'")

    # Call the data layer — handles fuzzy matching and fallback
    results = filter_providers(service=service, location=location)

    if DEBUG:
        print(f"[ProviderAgent] Found {len(results)} matching providers")

    return results
