"""Chat API router — handles messages and SSE streaming."""
from __future__ import annotations
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import MessageCreate, ChatHistoryResponse, MessageResponse
from services.chat_service import ChatService
from services.session_store import SessionStore
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])
@router.post("/{session_id}/message")
async def send_message(
    session_id: str,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and stream back the pipeline response via SSE.
    The response is a Server-Sent Events stream. Each event has:
    - event: message | pipeline_update | preview | error | export | complete
    - data: JSON payload
    """
    service = ChatService(db)
    async def event_generator():
        try:
            async for event in service.process_message(
                session_id, message.content, message.file_ids
            ):
                event_type = event.get("event", "message")
                event_data = json.dumps(event.get("data", {}))
                yield f"event: {event_type}\ndata: {event_data}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)[:500]})}\n\n"
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    store = SessionStore(db)
    messages = await store.get_messages(session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                message_type=m.message_type,
                metadata=m.metadata_ or {},
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
