"""Session store service for managing chat sessions in the database."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import Session, Message, UploadedFile
def _new_id() -> str:
    return str(uuid.uuid4())
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
class SessionStore:
    """Manages CRUD operations for sessions, messages, and files."""
    def __init__(self, db: AsyncSession):
        self.db = db
    # ── Sessions ──────────────────────────────────────────────────────
    async def create_session(self, title: str = "New Chat") -> Session:
        session = Session(id=_new_id(), title=title, context={}, created_at=_utcnow(), updated_at=_utcnow())
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    async def get_session(self, session_id: str) -> Session | None:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()
    async def list_sessions(self) -> list[Session]:
        result = await self.db.execute(select(Session).order_by(Session.updated_at.desc()))
        return list(result.scalars().all())
    async def update_session_context(self, session_id: str, context: dict) -> Session | None:
        session = await self.get_session(session_id)
        if session is None:
            return None
        # Merge context rather than overwrite
        existing = session.context or {}
        existing.update(context)
        session.context = existing
        session.updated_at = _utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session
    async def update_session_title(self, session_id: str, title: str) -> Session | None:
        session = await self.get_session(session_id)
        if session is None:
            return None
        session.title = title
        session.updated_at = _utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session
    async def delete_session(self, session_id: str) -> bool:
        result = await self.db.execute(delete(Session).where(Session.id == session_id))
        await self.db.commit()
        return result.rowcount > 0
    # ── Messages ──────────────────────────────────────────────────────
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: dict | None = None,
    ) -> Message:
        msg = Message(
            id=_new_id(),
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_=metadata or {},
            created_at=_utcnow(),
        )
        self.db.add(msg)
        # Update session timestamp
        session = await self.get_session(session_id)
        if session:
            session.updated_at = _utcnow()
        await self.db.commit()
        await self.db.refresh(msg)
        return msg
    async def get_messages(self, session_id: str) -> list[Message]:
        result = await self.db.execute(
            select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
        )
        return list(result.scalars().all())
    async def get_conversation_context(self, session_id: str, max_messages: int = 20) -> list[dict]:
        """Get recent messages formatted for AI context."""
        messages = await self.get_messages(session_id)
        recent = messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]
    # ── Files ─────────────────────────────────────────────────────────
    async def add_file(
        self,
        session_id: str,
        original_name: str,
        stored_path: str,
        file_type: str,
        file_size: int = 0,
    ) -> UploadedFile:
        f = UploadedFile(
            id=_new_id(),
            session_id=session_id,
            original_name=original_name,
            stored_path=stored_path,
            file_type=file_type,
            file_size=str(file_size),
            created_at=_utcnow(),
        )
        self.db.add(f)
        await self.db.commit()
        await self.db.refresh(f)
        return f
    async def get_files(self, session_id: str) -> list[UploadedFile]:
        result = await self.db.execute(
            select(UploadedFile).where(UploadedFile.session_id == session_id)
        )
        return list(result.scalars().all())
