# =============================================================
# _model.py — Shared Gemini model setup for all agents
#
# Creates a reusable OpenAIChatCompletionsModel pointed at
# Gemini's OpenAI-compatible endpoint via the official Agents SDK.
# Import this in each agent instead of duplicating setup code.
# =============================================================

import openai
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from app.config.settings import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL


def get_gemini_model() -> OpenAIChatCompletionsModel:
    """
    Build an OpenAIChatCompletionsModel that points to Gemini's
    OpenAI-compatible endpoint.

    Usage in any agent:
        from app.agents._model import get_gemini_model
        model = get_gemini_model()
        agent = Agent(name="...", instructions="...", model=model, output_type=MySchema)
    """
    # Async client configured for Gemini's endpoint
    client = openai.AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL,
    )

    # Wrap it in the SDK's model class so Agent / Runner can use it
    return OpenAIChatCompletionsModel(
        model=GEMINI_MODEL,
        openai_client=client,
    )
