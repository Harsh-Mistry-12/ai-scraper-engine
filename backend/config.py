"""Application configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "scraper.db"
# Create directories
for d in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)
# ── API Keys ───────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Fallback models to try when the primary model returns 503/429/overloaded.
# Tried in order: primary → fallback1 → fallback2 → ...
GEMINI_FALLBACK_MODELS: list[str] = os.getenv(
    "GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash"
).split(",")
# ── AI Retry Settings ─────────────────────────────────────────────────────
AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "3"))
AI_RETRY_BASE_DELAY: float = float(os.getenv("AI_RETRY_BASE_DELAY", "2.0"))  # seconds
# ── Server ─────────────────────────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
# ── Scraping defaults ─────────────────────────────────────────────────────
MAX_CONCURRENT_PAGES: int = int(os.getenv("MAX_CONCURRENT_PAGES", "5"))
REQUEST_DELAY_MS: int = int(os.getenv("REQUEST_DELAY_MS", "1000"))
REQUEST_TIMEOUT_S: int = int(os.getenv("REQUEST_TIMEOUT_S", "30"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
# ── Database ───────────────────────────────────────────────────────────────
DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH}"