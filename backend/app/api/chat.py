from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.auth import get_current_user
from app.services.streaming import StreamingService

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default_session"

@router.post("/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Accepts a user query and streams back the LLM response token-by-token
    using Server-Sent Events (SSE).
    """
    # In a full orchestration flow, the query would first pass through the
    # Intent, Cost, and Model Selection agents before hitting this streaming service.
    
    streamer = StreamingService()
    
    return StreamingResponse(
        streamer.stream_chat(request.query),
        media_type="text/event-stream"
    )
