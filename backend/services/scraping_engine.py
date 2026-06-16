"""Scraping engine — executes the scraping strategy using the appropriate technique."""
from __future__ import annotations
import asyncio
import logging
import json
from typing import Any, AsyncGenerator
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from utils.anti_detection import get_default_headers, rate_limited_delay, get_playwright_stealth_script
import config
logger = logging.getLogger(__name__)
class ScrapingEngine:
    """Executes scraping strategies and yields progress updates."""
    async def scrape(
        self,
        strategy: dict[str, Any],
        target_url: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute a scraping strategy and yield progress updates.
        Yields dicts with:
        - type: 'progress' | 'data' | 'error' | 'complete'
        - detail: description of what's happening
        - progress: 0.0-1.0
        - data: list of scraped rows (for 'data' type)
        """
        technique = strategy.get("technique", "direct_http")
        if technique == "direct_http":
            async for update in self._scrape_direct(strategy, target_url):
                yield update
        elif technique == "browser_automation":
            async for update in self._scrape_browser(strategy, target_url):
                yield update
        elif technique == "api_integration":
            async for update in self._scrape_api(strategy, target_url):
                yield update
        else:
            yield {"type": "error", "detail": f"Unknown technique: {technique}"}
    async def _scrape_direct(
        self,
        strategy: dict[str, Any],
        target_url: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Scrape using direct HTTP requests + BeautifulSoup."""
        selectors = strategy.get("selectors", {})
        container = strategy.get("container_selector", "")
        pagination = strategy.get("pagination", {"type": "none"})
        max_pages = pagination.get("max_pages", 10)
        all_data: list[dict[str, Any]] = []
        current_url = target_url
        page = 1
        yield {"type": "progress", "detail": "Starting HTTP scraping...", "progress": 0.0}
        async with httpx.AsyncClient(
            headers=get_default_headers(target_url),
            follow_redirects=True,
            timeout=config.REQUEST_TIMEOUT_S,
            verify=False,
        ) as client:
            while current_url and page <= max_pages:
                yield {
                    "type": "progress",
                    "detail": f"Fetching page {page}/{max_pages}...",
                    "progress": (page - 1) / max_pages,
                }
                try:
                    response = await client.get(current_url)
                    response.raise_for_status()
                except Exception as e:
                    yield {"type": "error", "detail": f"Failed to fetch page {page}: {str(e)[:200]}"}
                    break
                soup = BeautifulSoup(response.text, "html.parser")
                page_data = self._extract_data(soup, selectors, container)
                all_data.extend(page_data)
                yield {
                    "type": "progress",
                    "detail": f"Extracted {len(page_data)} items from page {page}. Total: {len(all_data)}",
                    "progress": page / max_pages,
                }
                # Handle pagination
                current_url = self._get_next_page(soup, pagination, current_url, page)
                page += 1
                if current_url:
                    await rate_limited_delay(config.REQUEST_DELAY_MS)
        if all_data:
            yield {"type": "data", "data": all_data, "detail": f"Scraped {len(all_data)} items total"}
            yield {"type": "complete", "detail": f"Scraping complete. {len(all_data)} items extracted."}
        else:
            yield {"type": "error", "detail": "No data was extracted. The selectors may need adjustment."}
    async def _scrape_browser(
        self,
        strategy: dict[str, Any],
        target_url: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Scrape using Playwright browser automation."""
        selectors = strategy.get("selectors", {})
        container = strategy.get("container_selector", "")
        wait_for = strategy.get("wait_for_selector", "")
        pagination = strategy.get("pagination", {"type": "none"})
        max_pages = pagination.get("max_pages", 10)
        all_data: list[dict[str, Any]] = []
        yield {"type": "progress", "detail": "Launching browser...", "progress": 0.0}
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=get_default_headers()["User-Agent"],
                    viewport={"width": 1920, "height": 1080},
                )
                page = await context.new_page()
                # Add stealth script
                await page.add_init_script(get_playwright_stealth_script())
                yield {"type": "progress", "detail": "Navigating to page...", "progress": 0.1}
                await page.goto(target_url, wait_until="networkidle", timeout=30000)
                # Wait for dynamic content
                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=10000)
                    except Exception:
                        yield {"type": "progress", "detail": "Wait selector timed out, proceeding...", "progress": 0.15}
                current_page = 1
                while current_page <= max_pages:
                    yield {
                        "type": "progress",
                        "detail": f"Extracting data from page {current_page}...",
                        "progress": 0.2 + (current_page - 1) / max_pages * 0.7,
                    }
                    # Get page HTML and extract
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    page_data = self._extract_data(soup, selectors, container)
                    all_data.extend(page_data)
                    yield {
                        "type": "progress",
                        "detail": f"Found {len(page_data)} items on page {current_page}. Total: {len(all_data)}",
                        "progress": 0.2 + current_page / max_pages * 0.7,
                    }
                    # Handle pagination
                    if pagination.get("type") == "next_button" and pagination.get("selector"):
                        next_btn = await page.query_selector(pagination["selector"])
                        if next_btn and await next_btn.is_visible():
                            await next_btn.click()
                            await page.wait_for_load_state("networkidle")
                            await rate_limited_delay(config.REQUEST_DELAY_MS)
                            current_page += 1
                        else:
                            break
                    elif pagination.get("type") == "infinite_scroll":
                        prev_height = await page.evaluate("document.body.scrollHeight")
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        if new_height == prev_height:
                            break
                        current_page += 1
                    else:
                        break
                await browser.close()
        except ImportError:
            yield {"type": "error", "detail": "Playwright is not installed. Run: playwright install chromium"}
            return
        except Exception as e:
            yield {"type": "error", "detail": f"Browser scraping error: {str(e)[:300]}"}
            return
        if all_data:
            yield {"type": "data", "data": all_data, "detail": f"Scraped {len(all_data)} items total"}
            yield {"type": "complete", "detail": f"Browser scraping complete. {len(all_data)} items extracted."}
        else:
            yield {"type": "error", "detail": "No data extracted via browser. Selectors may need adjustment."}
    async def _scrape_api(
        self,
        strategy: dict[str, Any],
        target_url: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Scrape using discovered API endpoints."""
        api_details = strategy.get("api_details", {})
        endpoints = api_details.get("endpoints", [])
        if not endpoints:
            yield {"type": "error", "detail": "No API endpoints provided in strategy."}
            return
        all_data: list[dict[str, Any]] = []
        yield {"type": "progress", "detail": f"Calling {len(endpoints)} API endpoint(s)...", "progress": 0.0}
        async with httpx.AsyncClient(
            headers=get_default_headers(target_url),
            follow_redirects=True,
            timeout=config.REQUEST_TIMEOUT_S,
            verify=False,
        ) as client:
            for i, endpoint in enumerate(endpoints):
                # Make endpoint absolute
                if endpoint.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(target_url)
                    endpoint = f"{parsed.scheme}://{parsed.netloc}{endpoint}"
                yield {
                    "type": "progress",
                    "detail": f"Calling API: {endpoint[:100]}...",
                    "progress": (i + 1) / len(endpoints),
                }
                try:
                    response = await client.get(endpoint)
                    data = response.json()
                    if isinstance(data, list):
                        all_data.extend(data)
                    elif isinstance(data, dict):
                        # Try common patterns for nested data
                        for key in ["data", "results", "items", "records", "rows"]:
                            if key in data and isinstance(data[key], list):
                                all_data.extend(data[key])
                                break
                        else:
                            all_data.append(data)
                except Exception as e:
                    yield {"type": "progress", "detail": f"API call failed: {str(e)[:200]}", "progress": (i + 1) / len(endpoints)}
                await rate_limited_delay(config.REQUEST_DELAY_MS)
        if all_data:
            yield {"type": "data", "data": all_data, "detail": f"Got {len(all_data)} records from API"}
            yield {"type": "complete", "detail": f"API scraping complete. {len(all_data)} records retrieved."}
        else:
            yield {"type": "error", "detail": "No data retrieved from API endpoints."}
    def _extract_data(
        self,
        soup: BeautifulSoup,
        selectors: dict[str, str],
        container_selector: str = "",
    ) -> list[dict[str, Any]]:
        """Extract data from HTML using CSS selectors."""
        data = []
        if container_selector:
            containers = soup.select(container_selector)
            for container in containers:
                row = {}
                for field, selector in selectors.items():
                    try:
                        element = container.select_one(selector)
                        if element:
                            # Try to get href for links, src for images, text otherwise
                            if element.name == "a" and element.get("href"):
                                row[field] = element.get("href", "").strip()
                            elif element.name == "img" and element.get("src"):
                                row[field] = element.get("src", "").strip()
                            else:
                                row[field] = element.get_text(strip=True)
                        else:
                            row[field] = ""
                    except Exception:
                        row[field] = ""
                if any(v for v in row.values()):
                    data.append(row)
        else:
            # No container — try to extract each field independently
            row = {}
            for field, selector in selectors.items():
                try:
                    elements = soup.select(selector)
                    if len(elements) == 1:
                        row[field] = elements[0].get_text(strip=True)
                    elif len(elements) > 1:
                        # If multiple elements, create rows
                        for i, el in enumerate(elements):
                            if i >= len(data):
                                data.append({})
                            data[i][field] = el.get_text(strip=True)
                except Exception:
                    pass
            if row and not data:
                data.append(row)
        return data
    def _get_next_page(
        self,
        soup: BeautifulSoup,
        pagination: dict[str, Any],
        current_url: str,
        current_page: int,
    ) -> str | None:
        """Determine the next page URL based on pagination config."""
        ptype = pagination.get("type", "none")
        if ptype == "none":
            return None
        if ptype == "next_button":
            selector = pagination.get("selector", "")
            if selector:
                next_el = soup.select_one(selector)
                if next_el and next_el.get("href"):
                    return urljoin(current_url, next_el["href"])
            return None
        if ptype == "url_parameter":
            pattern = pagination.get("url_pattern", "")
            if pattern:
                next_url = pattern.replace("{page}", str(current_page + 1))
                return urljoin(current_url, next_url)
            return None
        return None
