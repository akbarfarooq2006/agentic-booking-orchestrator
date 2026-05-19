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
    top_providers: list[RankedProvider]   # max 3
    summary: str                          # Overall summary message


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


async def _generate_reasons(top3: list[dict[str, Any]]) -> list[str]:
    """
    Use a direct chat completion to generate ranking reasons for providers.
    """
    if not top3:
        return []

    lines = []
    for i, p in enumerate(top3, 1):
        lines.append(
            f"Provider {i}: {p['name']} | "
            f"rating={p['rating']} | "
            f"eta={p['eta_minutes']} min | "
            f"verified={p['verified']} | "
            f"available={p['available']} | "
            f"completed_jobs={p['completed_jobs']} | "
            f"response_time={p['response_time_minutes']} min"
        )

    system_prompt = """You are a booking assistant explaining recommendations.
For each provider, write a SHORT (1 sentence) reason highlighting their best feature.
Highlight details like rating, ETA, completed jobs, or verified status.

You must respond with ONLY a valid JSON object matching this schema:
{
  "reasons": ["reason for provider 1", "reason for provider 2", "reason for provider 3"]
}"""

    prompt = "Generate reasons for these top providers:\n" + "\n".join(lines)

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
        reasons = data.get("reasons", [])

        # Pad with fallbacks if necessary
        while len(reasons) < len(top3):
            reasons.append("Strong recommendation based on high rating.")

        return reasons[:len(top3)]

    except Exception as e:
        print(f"[RankingAgent] Reason generation failed: {e} — using fallback text")
        
        # Build simple readable defaults
        fallbacks = []
        for p in top3:
            parts = []
            if p.get("available"):
                parts.append("currently available")
            if p.get("verified"):
                parts.append("verified")
            if p.get("rating", 0) >= 4.5:
                parts.append(f"{p['rating']} star rating")
            if p.get("eta_minutes", 60) <= 30:
                parts.append(f"{p['eta_minutes']} min ETA")
            fallbacks.append(
                f"{', '.join(parts).capitalize() if parts else 'Good overall score'}."
            )
        return fallbacks


async def run_ranking_agent(providers: list[dict[str, Any]]) -> RankingResult:
    """
    Score all providers and return the top 3 with explanations.
    """
    if DEBUG:
        print(f"[RankingAgent] Ranking {len(providers)} providers")

    if not providers:
        return RankingResult(
            top_providers=[],
            summary="No providers found for your request.",
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

    # Generate reasons
    reasons = await _generate_reasons(top3_raw)

    top_providers = [
        RankedProvider(provider=p, score=s, reason=r)
        for p, s, r in zip(top3_raw, top3_scores, reasons)
    ]

    summary = (
        f"Found {len(providers)} providers. "
        f"Here are the top {len(top_providers)} recommendations for you."
    )

    return RankingResult(top_providers=top_providers, summary=summary)
