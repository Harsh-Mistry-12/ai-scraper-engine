"""Anti-detection utilities for ethical web scraping."""
from __future__ import annotations
import random
import asyncio
from typing import Any
# Curated list of real-world User-Agent strings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]
def get_random_user_agent() -> str:
    """Return a random User-Agent string."""
    return random.choice(USER_AGENTS)
def get_default_headers(referer: str | None = None) -> dict[str, str]:
    """Return realistic browser headers for HTTP requests."""
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    return headers
async def rate_limited_delay(base_ms: int = 1000, jitter_ms: int = 500) -> None:
    """Sleep with a random jitter to avoid pattern detection."""
    delay = (base_ms + random.randint(0, jitter_ms)) / 1000.0
    await asyncio.sleep(delay)
def check_robots_txt(robots_content: str, url_path: str, user_agent: str = "*") -> bool:
    """
    Basic robots.txt parser. Returns True if the path is allowed.
    This is a simplified parser for common cases.
    """
    if not robots_content:
        return True
    lines = robots_content.strip().split("\n")
    current_agent_matches = False
    disallowed_paths: list[str] = []
    allowed_paths: list[str] = []
    for line in lines:
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agent_matches = agent == "*" or agent.lower() in user_agent.lower()
        elif current_agent_matches:
            if line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed_paths.append(path)
            elif line.lower().startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    allowed_paths.append(path)
    # Check allowed first (more specific)
    for path in allowed_paths:
        if url_path.startswith(path):
            return True
    # Then check disallowed
    for path in disallowed_paths:
        if url_path.startswith(path):
            return False
    return True
def get_playwright_stealth_script() -> str:
    """Return JavaScript to make Playwright less detectable."""
    return """
    // Override webdriver property
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    // Override plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    // Override languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    // Override chrome property
    window.chrome = { runtime: {} };
    // Override permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
    """
