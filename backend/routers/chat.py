from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.scraping_pipeline import ScrapingPipeline
import json

router = APIRouter(prefix="/ws", tags=["chat"])
pipeline = ScrapingPipeline()

@router.websocket("/chat/{session_id}")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "text":
                    prompt = message.get("content", "")
                    await pipeline.run_pipeline(prompt, session_id, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
        # Handle disconnection
