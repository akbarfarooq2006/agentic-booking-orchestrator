# =============================================================
# orchestrator.py — Main workflow controller
#
# Every user message flows through here FIRST.
# The orchestrator decides which agents to call and in what order.
# It manages conversation state across turns.
# =============================================================

from typing import Any
from pydantic import BaseModel, Field
from app.agents.intent_agent import run_intent_agent, IntentResult
from app.agents.clarification_agent import run_clarification_agent
from app.agents.provider_agent import run_provider_agent
from app.agents.ranking_agent import run_ranking_agent, RankingResult
from app.agents.booking_agent import run_booking_agent
from app.config.settings import DEBUG


# ------------------------------------------------------------------
# Conversation State — persisted client-side, echoed back each turn
# ------------------------------------------------------------------
class ConversationState(BaseModel):
    service: str | None = None                  # Extracted service type
    location: str | None = None                 # Extracted location
    time: str | None = None                     # Extracted time preference
    urgency: str = "normal"                     # "normal" | "urgent"
    selected_provider: dict | None = None       # Provider chosen by user
    providers_shown: list[dict] = Field(default_factory=list)  # Top providers from last search
    step: str = "start"                         # Workflow step tracker
    # step values:
    #   "start"             → fresh conversation
    #   "clarifying"        → waiting for user to answer clarification question
    #   "showing_providers" → providers were returned, waiting for user to pick one
    #   "booked"            → booking confirmed


# ------------------------------------------------------------------
# Orchestrator response shape
# ------------------------------------------------------------------
class OrchestratorResponse(BaseModel):
    reply: str                                  # Message to show the user
    providers: list[dict] = []                  # Top providers (empty if not at that step)
    state: ConversationState                    # Updated state to echo back next turn


# ------------------------------------------------------------------
# Helper: detect booking intent from message
# ------------------------------------------------------------------
_BOOKING_KEYWORDS = [
    "book", "confirm", "yes", "book this", "go ahead",
    "hire", "select", "choose", "ok book", "yes book",
]

def _user_wants_to_book(message: str, providers_shown: list[dict]) -> dict[str, Any] | None:
    """
    Check if the user is trying to book a provider.

    Returns the provider dict if we can determine which one,
    otherwise None.

    Detection strategies:
    1. User says "book the first one" / "book #1" / "book 1"
    2. User mentions a provider name from providers_shown
    3. User says "yes" or "confirm" and there's exactly 1 provider shown
    """
    if not providers_shown:
        return None

    msg_lower = message.lower().strip()

    # Strategy 1: "first", "1", "#1", "top one"
    if any(k in msg_lower for k in ["first", "#1", " 1", "top one", "number 1", "1st"]):
        return providers_shown[0]

    # Strategy 2: "second", "2", "#2"
    if len(providers_shown) >= 2 and any(k in msg_lower for k in ["second", "#2", " 2", "number 2", "2nd"]):
        return providers_shown[1]

    # Strategy 3: "third", "3", "#3"
    if len(providers_shown) >= 3 and any(k in msg_lower for k in ["third", "#3", " 3", "number 3", "3rd"]):
        return providers_shown[2]

    # Strategy 4: Provider name mentioned
    for provider in providers_shown:
        pname = provider.get("name", "").lower()
        if pname and pname in msg_lower:
            return provider

    # Strategy 5: Generic "yes"/"confirm"/"book" with single provider shown
    has_booking_keyword = any(k in msg_lower for k in _BOOKING_KEYWORDS)
    if has_booking_keyword:
        # If there's only one provider or user clearly confirms
        return providers_shown[0]  # Default to first provider

    return None


# ------------------------------------------------------------------
# Helper: format provider list as a readable reply string
# ------------------------------------------------------------------
# Main orchestrator function — called by the /chat route
# ------------------------------------------------------------------
async def run_orchestrator(
    user_message: str,
    state: ConversationState,
) -> OrchestratorResponse:
    """
    Central workflow controller.

    Decision tree:
    1. If already booked → friendly message, no re-processing
    2. If user is trying to book a provider → run booking agent
    3. If we already have service + location → skip to provider search
    4. Otherwise → run intent + clarification agents
       a. If clarification needed → return question, stop here
       b. If all info present → run provider + ranking agents

    Args:
        user_message: Raw text from the user.
        state:        Current conversation state (echoed from client).

    Returns:
        OrchestratorResponse with reply, providers, and updated state.
    """
    if DEBUG:
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Message: '{user_message}'")
        print(f"[Orchestrator] State: {state.model_dump()}")

    # ----------------------------------------------------------------
    # STEP 0: Already booked — don't re-process
    # ----------------------------------------------------------------
    if state.step == "booked":
        return OrchestratorResponse(
            reply=(
                f"You already have a confirmed booking! "
                f"If you need another service, just tell me what you need."
            ),
            providers=[],
            state=state,
        )

    # ----------------------------------------------------------------
    # STEP 1: Check if user is selecting/booking a provider
    # ----------------------------------------------------------------
    if state.step == "showing_providers" and state.providers_shown:
        selected = _user_wants_to_book(user_message, state.providers_shown)
        if selected:
            if DEBUG:
                print(f"[Orchestrator] User selected: {selected.get('name')}")

            booking = await run_booking_agent(selected)

            state.selected_provider = selected
            state.step = "booked"

            return OrchestratorResponse(
                reply=booking.message,
                providers=[],
                state=state,
            )

    # ----------------------------------------------------------------
    # STEP 2: Extract intent from the user's message
    # (Always run intent extraction to pick up new info)
    # ----------------------------------------------------------------
    # Build chat history summary for context
    history = ""
    if state.service:
        history += f"User previously mentioned service: {state.service}. "
    if state.location:
        history += f"Location: {state.location}. "
    if state.time:
        history += f"Time preference: {state.time}. "

    intent: IntentResult = await run_intent_agent(user_message, history)
    if DEBUG:
        print(f"[Orchestrator] Intent: {intent.model_dump()}")

    # --- Update state with any newly extracted fields ---
    # Merge: new intent values override old ones only if non-null
    if intent.service:
        state.service = intent.service
    if intent.location:
        state.location = intent.location
    if intent.time:
        state.time = intent.time
    if intent.urgency:
        state.urgency = intent.urgency

    # ----------------------------------------------------------------
    # STEP 3: Clarification check
    # ----------------------------------------------------------------
    clarification = await run_clarification_agent(intent, user_message)

    if clarification.needs_clarification:
        # Still missing required fields — ask the user
        state.step = "clarifying"
        if DEBUG:
            print(f"[Orchestrator] Needs clarification: {clarification.missing_fields}")

        return OrchestratorResponse(
            reply=clarification.question,
            providers=[],
            state=state,
        )

    # ----------------------------------------------------------------
    # STEP 4: Search providers
    # ----------------------------------------------------------------
    if DEBUG:
        print(f"[Orchestrator] Searching providers: {state.service} in {state.location}")

    providers = await run_provider_agent(state.service, state.location)

    if not providers:
        return OrchestratorResponse(
            reply=(
                f"I couldn't find any {state.service} providers in {state.location}. "
                f"Try a nearby area or a different service type."
            ),
            providers=[],
            state=state,
        )

    # ----------------------------------------------------------------
    # STEP 5: Rank providers and return top 3
    # ----------------------------------------------------------------
    ranking: RankingResult = await run_ranking_agent(providers, user_message)

    # Store the top providers in state for the booking step
    state.providers_shown = ranking.top_providers
    state.step = "showing_providers"

    return OrchestratorResponse(
        reply=ranking.formatted_reply,
        providers=ranking.top_providers,
        state=state,
    )
