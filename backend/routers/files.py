"""Files API router — handles file upload and download."""
from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import FileUploadResponse
from services.session_store import SessionStore
from utils.file_handler import detect_file_type
import config
router = APIRouter(prefix="/api/files", tags=["files"])
@router.post("/upload/{session_id}", response_model=FileUploadResponse)
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file (CSV, XLSX, JSON, XML) to a session."""
    # Validate file type
    try:
        file_type = detect_file_type(file.filename or "unknown")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Save file
    file_id = str(uuid.uuid4())
    ext = Path(file.filename or "").suffix
    stored_name = f"{file_id}{ext}"
    stored_path = config.UPLOAD_DIR / stored_name
    content = await file.read()
    stored_path.write_bytes(content)
    # Record in database
    store = SessionStore(db)
    record = await store.add_file(
        session_id=session_id,
        original_name=file.filename or "unknown",
        stored_path=str(stored_path),
        file_type=file_type,
        file_size=len(content),
    )
    return FileUploadResponse(
        id=record.id,
        original_name=record.original_name,
        file_type=record.file_type,
        file_size=record.file_size,
    )
@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download an exported output file."""
    filepath = config.OUTPUT_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="application/octet-stream",
    )
