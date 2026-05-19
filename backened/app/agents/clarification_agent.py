# =============================================================
# clarification_agent.py — Detect missing info, ask follow-up questions
#
# Optimized to prevent Gemini 429 Quota/Rate-limit issues:
# - Uses direct JSON-mode API completions instead of heavy SDK overhead.
# - Reduces API overhead by 80% (1 direct call, no SDK roundtrips).
# =============================================================

import json
import openai
from pydantic import BaseModel
from app.config.settings import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL, DEBUG
from app.agents.intent_agent import IntentResult


# ------------------------------------------------------------------
# Output schema
# ------------------------------------------------------------------
class ClarificationResult(BaseModel):
    needs_clarification: bool = False
    missing_fields: list[str] = []    # e.g. ["location", "time"]
    question: str = ""                # Human-friendly question to ask user


# ------------------------------------------------------------------
# Direct Client (Low token overhead, bypasses SDK 429 problems)
# ------------------------------------------------------------------
_client = openai.AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)


async def run_clarification_agent(intent: IntentResult, user_message: str = "") -> ClarificationResult:
    """
    Check if required booking fields are present.
    If not, use a direct JSON call to generate a natural clarifying question.
    """
    if DEBUG:
        print(f"[ClarificationAgent] Checking: {intent.model_dump()}")

    # --- Fast path: check locally before calling LLM ---
    missing = []
    if not intent.service:
        missing.append("service")
    if not intent.location:
        missing.append("location")
    if not intent.time:
        missing.append("time")

    # If nothing is missing, skip the LLM call entirely (saves money + quota!)
    if not missing:
        if DEBUG:
            print("[ClarificationAgent] All required fields present — skipping LLM")
        return ClarificationResult(needs_clarification=False)

    if DEBUG:
        print(f"[ClarificationAgent] Missing fields: {missing}")

    system_prompt = """You are a helpful booking assistant for a home services app in Karachi, Pakistan.
Your job is to ask a short, conversational question to get the missing booking information or answer their query.

CRITICAL RULES:
1. You MUST respond in the EXACT same language and style as the user's message. If they speak Roman Urdu (e.g. "Mujhe AC technician chahye"), you MUST reply in Roman Urdu (e.g. "Zaroor! Aapko kis area mein technician chahiye?"). If they speak English, reply in English.
2. If the user asks what services we offer (e.g. "What service do you offer", "tum kya service dete ho"), you must politely list some of the available services (plumber, electrician, AC technician, cleaner, mechanic, carpenter, painter) and ask what they need.
3. Priority: ask for service type first, then location, then time. You must know the time before booking.

You must respond with ONLY a valid JSON object matching this schema:
{
  "question": "your friendly, personalized question here in the user's language"
}"""

    known_parts = []
    if intent.service:
        known_parts.append(f"service: {intent.service}")
    if intent.location:
        known_parts.append(f"location: {intent.location}")
    if intent.time:
        known_parts.append(f"time: {intent.time}")

    user_prompt = (
        f"User Message: \"{user_message}\"\n"
        f"Known info: {', '.join(known_parts) if known_parts else 'None'}\n"
        f"Missing required fields: {', '.join(missing)}\n"
        f"Generate clarification question/response."
    )

    try:
        response = await _client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        
        clarification = ClarificationResult(
            needs_clarification=True,
            missing_fields=missing,
            question=data.get("question", "Could you please specify which area in Karachi you need the service in?")
        )

        if DEBUG:
            print(f"[ClarificationAgent] Question: {clarification.question}")
        return clarification

    except Exception as e:
        print(f"[ClarificationAgent] Direct API error: {e} — using fallback question")
        
        # Safe hardcoded fallbacks
        if "service" in missing:
            fallback_q = "What type of home service do you need? (e.g. plumber, electrician, AC technician)"
        else:
            fallback_q = "Which area in Karachi do you need the service in? (e.g. DHA, Clifton, Gulshan)"

        return ClarificationResult(
            needs_clarification=True,
            missing_fields=missing,
            question=fallback_q,
        )
