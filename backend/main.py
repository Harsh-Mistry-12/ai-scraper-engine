"""FastAPI application — AI Scraper Engine backend."""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config
from models.database import init_db
from routers import chat, sessions, files
# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
# ── Lifecycle ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting AI Scraper Engine...")
    await init_db()
    logger.info("✅ Database initialized")
    if not config.GEMINI_API_KEY:
        logger.warning("⚠️  GEMINI_API_KEY not set — AI features will not work!")
    yield
    logger.info("👋 Shutting down AI Scraper Engine")
# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Scraper Engine",
    description="AI-powered web scraping through a conversational interface",
    version="1.0.0",
    lifespan=lifespan,
)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Routers
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(files.router)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Scraper Engine",
        "gemini_configured": bool(config.GEMINI_API_KEY),
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
