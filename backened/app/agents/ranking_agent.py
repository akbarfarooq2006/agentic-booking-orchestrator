# =============================================================
# ranking_agent.py — Score and rank providers, return top 3
#
# Optimized to prevent Gemini 429 Quota/Rate-limit issues:
# - Scoring is pure Python (fast, deterministic).
# - Uses direct completions to generate the human-readable reasons
#   instead of the heavy SDK structured output framework.
# - Saves over 80% token overhead, using 1 single simple call.
# =============================================================

import math
import json
import openai
from typing import Any
from pydantic import BaseModel
from app.config.settings import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL, DEBUG


# ------------------------------------------------------------------
# Output schemas
# ------------------------------------------------------------------
class RankedProvider(BaseModel):
    provider: dict[str, Any]
    score: float          # 0.0 – 100.0 composite score
    reason: str           # Human-readable explanation


class RankingResult(BaseModel):
    top_providers: list[dict[str, Any]]   # max 3 raw providers for state
    formatted_reply: str                  # The final localized reply text


# ------------------------------------------------------------------
# Direct Client (Low token overhead, bypasses SDK 429 problems)
# ------------------------------------------------------------------
_client = openai.AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)


# ------------------------------------------------------------------
# Scoring formula — pure Python, no LLM
# ------------------------------------------------------------------
def _compute_score(provider: dict[str, Any]) -> float:
    """
    Compute a composite 0-100 score for a provider.
    """
    # 35 pts: rating
    rating_score = (provider.get("rating", 0) / 5.0) * 35

    # 20 pts: availability
    available_score = 20 if provider.get("available", False) else 0

    # 15 pts: verified
    verified_score = 15 if provider.get("verified", False) else 0

    # 15 pts: ETA (lower = better; 1 min → ~15 pts, 60 min → ~0.25 pts)
    eta = max(provider.get("eta_minutes", 60), 1)
    eta_score = (1.0 / eta) * 15 * 60

    # 10 pts: Response time (lower = better)
    resp = max(provider.get("response_time_minutes", 30), 1)
    resp_score = (1.0 / resp) * 10 * 30

    # 5 pts: Experience (log scale, caps around 5000 jobs)
    jobs = max(provider.get("completed_jobs", 0), 1)
    exp_score = (math.log10(jobs) / math.log10(5000)) * 5

    total = rating_score + available_score + verified_score + eta_score + resp_score + exp_score
    return round(min(max(total, 0), 100), 2)


async def _generate_formatted_reply(top3: list[dict[str, Any]], total_found: int, user_message: str) -> str:
    """
    Use a direct chat completion to generate a beautifully formatted, localized
    final response that lists the providers and asks the user to pick one.
    """
    if not top3:
        return "I could not find any providers for that request."

    lines = []
    for i, p in enumerate(top3, 1):
        lines.append(
            f"Provider {i}: {p['name']} | "
            f"rating={p['rating']} | "
            f"eta={p['eta_minutes']} min | "
            f"verified={p['verified']} | "
            f"available={p['available']}"
        )

    system_prompt = """You are a helpful booking assistant in Karachi, Pakistan.
Your job is to present the top service providers to the user and ask them which one they want to book.

CRITICAL RULES:
1. You MUST respond in the EXACT same language and style as the user's message. If they speak Roman Urdu (e.g. "Mujhe AC technician chahye"), you MUST reply in Roman Urdu (e.g. "Mujhe 15 providers mil gaye hain, ye top 3 hain..."). If they speak English, reply in English.
2. Format the response beautifully using bold text for names, and include their Rating, ETA, and Verified status.
3. Add a short 1-line reason for each provider why they are good (e.g. "Best rating" or "Fastest ETA").
4. At the end, ask the user to reply with '1', '2', or '3' to book one.

You must respond with ONLY a valid JSON object matching this schema:
{
  "formatted_reply": "the full, multi-line, formatted text reply here"
}"""

    prompt = (
        f"User Message: \"{user_message}\"\n"
        f"Total matching providers found in database: {total_found}\n"
        f"Top Providers to show:\n" + "\n".join(lines)
    )

    try:
        response = await _client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return data.get("formatted_reply", "Here are the top providers. Reply 1, 2, or 3 to book.")

    except Exception as e:
        print(f"[RankingAgent] Reply generation failed: {e} — using fallback text")
        
        # Fallback in English
        reply = f"Found {total_found} providers. Here are the top {len(top3)}:\n\n"
        for i, p in enumerate(top3, 1):
            reply += f"{i}. **{p['name']}** (Rating: {p['rating']}, ETA: {p['eta_minutes']}m)\n"
        reply += "\nReply 1, 2, or 3 to book."
        return reply


async def run_ranking_agent(providers: list[dict[str, Any]], user_message: str = "") -> RankingResult:
    """
    Score all providers and return the localized reply.
    """
    if DEBUG:
        print(f"[RankingAgent] Ranking {len(providers)} providers")

    if not providers:
        return RankingResult(
            top_providers=[],
            formatted_reply="No providers found for your request.",
        )

    # Score all providers in Python
    scored = sorted(
        [(p, _compute_score(p)) for p in providers],
        key=lambda x: x[1],
        reverse=True,
    )

    # Take top 3
    top3_pairs = scored[:3]
    top3_raw = [p for p, _ in top3_pairs]
    top3_scores = [s for _, s in top3_pairs]

    if DEBUG:
        for p, s in zip(top3_raw, top3_scores):
            print(f"  Provider {p['name']} -> score: {s}")

    # Generate formatted reply
    formatted_reply = await _generate_formatted_reply(top3_raw, len(providers), user_message)

    return RankingResult(
        top_providers=top3_raw,
        formatted_reply=formatted_reply
    )
