# =============================================================
# booking_agent.py — Simulate booking confirmation
#
# Pure Python — NO LLM calls needed.
# Generates a booking confirmation with a random booking ID.
# =============================================================

import random
import string
from typing import Any
from pydantic import BaseModel
from app.config.settings import DEBUG


# ------------------------------------------------------------------
# Output schema
# ------------------------------------------------------------------
class BookingResult(BaseModel):
    booking_status: str   # "confirmed" | "failed"
    provider_name: str
    eta: str              # e.g. "20 minutes"
    booking_id: str       # e.g. "BK-48291"
    message: str          # Human-friendly confirmation message


def _generate_booking_id() -> str:
    """Generate a random 5-digit booking ID like BK-48291."""
    digits = "".join(random.choices(string.digits, k=5))
    return f"BK-{digits}"


async def run_booking_agent(provider: dict[str, Any]) -> BookingResult:
    """
    Simulate a booking confirmation for the selected provider.

    Args:
        provider: The provider dict selected by the user.

    Returns:
        BookingResult with booking_id, eta, and confirmation message.
    """
    if DEBUG:
        print(f"[BookingAgent] Booking provider: {provider.get('name')}")

    provider_name = provider.get("name", "Unknown Provider")
    eta_minutes = provider.get("eta_minutes", 30)
    eta_str = f"{eta_minutes} minutes"

    # Simulate booking — in real system this would hit a database
    booking_id = _generate_booking_id()

    # Build a friendly confirmation message
    message = (
        f"Your booking is confirmed!\n"
        f"Provider: {provider_name}\n"
        f"Booking ID: {booking_id}\n"
        f"Estimated Arrival: {eta_str}\n"
        f"You will receive a confirmation shortly."
    )

    if DEBUG:
        print(f"[BookingAgent] Booking confirmed: {booking_id}")

    return BookingResult(
        booking_status="confirmed",
        provider_name=provider_name,
        eta=eta_str,
        booking_id=booking_id,
        message=message,
    )
