"""Pydantic schemas for API request/response validation."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
# ── Session Schemas ───────────────────────────────────────────────────────
class SessionCreate(BaseModel):
    title: str = "New Chat"
class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
# ── Message Schemas ───────────────────────────────────────────────────────
class MessageCreate(BaseModel):
    content: str
    file_ids: list[str] = Field(default_factory=list)
class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    message_type: str = "text"
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime
    class Config:
        from_attributes = True
        populate_by_name = True
class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageResponse]
# ── Pipeline Schemas ──────────────────────────────────────────────────────
class PipelineStep(BaseModel):
    name: str
    status: str = "pending"  # pending | running | completed | error
    detail: str = ""
    progress: Optional[float] = None  # 0.0 - 1.0
class PipelineState(BaseModel):
    steps: list[PipelineStep]
    current_step: int = 0
# ── Scraping Strategy ────────────────────────────────────────────────────
class ScrapingStrategy(BaseModel):
    technique: str = "direct_http"  # direct_http | browser_automation | api_integration
    target_url: str = ""
    selectors: dict[str, str] = Field(default_factory=dict)
    pagination: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    anti_scraping_notes: list[str] = Field(default_factory=list)
    api_details: Optional[dict[str, Any]] = None
# ── Data Preview ──────────────────────────────────────────────────────────
class DataPreview(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    preview_rows: int
class ApproveRequest(BaseModel):
    session_id: str
    output_format: str = "csv"  # csv | xlsx | json | xml
class ExportResponse(BaseModel):
    download_url: str
    filename: str
    format: str
    total_rows: int
# ── File Upload ───────────────────────────────────────────────────────────
class FileUploadResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    file_size: str
# ── SSE Event ─────────────────────────────────────────────────────────────
class SSEEvent(BaseModel):
    event: str  # pipeline_update | message | preview | error | complete
    data: dict[str, Any]
# ── Website Analysis ─────────────────────────────────────────────────────
class WebsiteAnalysis(BaseModel):
    url: str
    is_dynamic: bool = False
    has_api: bool = False
    api_details: Optional[dict[str, Any]] = None
    anti_scraping: list[str] = Field(default_factory=list)
    recommended_technique: str = "direct_http"
    robots_txt: Optional[str] = None
    page_title: str = ""
    content_type: str = ""
    notes: list[str] = Field(default_factory=list)
