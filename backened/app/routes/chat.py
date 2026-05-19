# =============================================================
# chat.py — FastAPI router for the /chat endpoint
#
# Single POST endpoint that receives a user message + optional state,
# passes everything through the orchestrator, and returns a reply.
# =============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.orchestrator import run_orchestrator, ConversationState, OrchestratorResponse
from app.config.settings import DEBUG

router = APIRouter()


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str                              # User's raw message
    state: ConversationState | None = None    # Previous conversation state (null on first turn)


class ChatResponse(BaseModel):
    reply: str                    # Text reply to show the user
    providers: list[dict] = []    # Top providers (empty during clarification / booking steps)
    state: ConversationState      # Updated state — client must echo this back next turn


# ------------------------------------------------------------------
# POST /chat
# ------------------------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint — every user message goes through the orchestrator.

    Request body:
        {
            "message": "Need AC technician in Clifton",
            "state": null  // or the state object from the previous response
        }

    Response:
        {
            "reply": "Here are the top providers...",
            "providers": [...],
            "state": { "service": "AC technician", "location": "Clifton", ... }
        }
    """
    if DEBUG:
        print(f"\n📨 [/chat] Received: '{request.message}'")

    # Use fresh state if none provided (first message in conversation)
    current_state = request.state or ConversationState()

    try:
        # Route through the orchestrator — all agent logic lives there
        result: OrchestratorResponse = await run_orchestrator(
            user_message=request.message,
            state=current_state,
        )

        if DEBUG:
            print(f"📤 [/chat] Reply: '{result.reply[:80]}...'")

        return ChatResponse(
            reply=result.reply,
            providers=result.providers,
            state=result.state,
        )

    except Exception as e:
        # Log the error and return a safe fallback — never crash the server
        print(f"❌ [/chat] Unhandled error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}",
        )
