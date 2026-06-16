"""Sessions API router — CRUD for chat sessions."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import SessionCreate, SessionResponse, SessionListResponse
from services.session_store import SessionStore
router = APIRouter(prefix="/api/sessions", tags=["sessions"])
@router.post("/", response_model=SessionResponse)
async def create_session(
    body: SessionCreate = SessionCreate(),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    store = SessionStore(db)
    session = await store.create_session(body.title)
    return session
@router.get("/", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all chat sessions, most recent first."""
    store = SessionStore(db)
    sessions = await store.list_sessions()
    return SessionListResponse(sessions=sessions)
@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific session by ID."""
    store = SessionStore(db)
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a session and all its messages."""
    store = SessionStore(db)
    deleted = await store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}
