"""SQLAlchemy database models and engine setup."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from config import DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
def utcnow():
    return datetime.now(timezone.utc)
class Session(Base):
    """A chat session that groups related messages and context together."""
    __tablename__ = "sessions"
    id = Column(String(36), primary_key=True)
    title = Column(String(255), default="New Chat")
    context = Column(JSON, default=dict)  # Stores extracted URL, fields, strategy, etc.
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan",
                            order_by="Message.created_at")
class Message(Base):
    """A single message within a chat session."""
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    message_type = Column(String(30), default="text")  # text | pipeline | preview | error
    metadata_ = Column("metadata", JSON, default=dict)  # Extra data (pipeline state, preview rows, etc.)
    created_at = Column(DateTime, default=utcnow)
    session = relationship("Session", back_populates="messages")
class UploadedFile(Base):
    """Tracks files uploaded by the user."""
    __tablename__ = "uploaded_files"
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    file_type = Column(String(20), nullable=False)  # csv | xlsx | json | xml
    file_size = Column(String(20), default="0")
    created_at = Column(DateTime, default=utcnow)
async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
async def get_db() -> AsyncSession:
    """Yield a database session."""
    async with async_session() as session:
        yield session