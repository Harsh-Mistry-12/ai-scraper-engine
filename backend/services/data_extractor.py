from playwright.async_api import async_playwright
import httpx
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

class DataExtractor:
    """
    Handles the actual data extraction using Playwright, httpx, or Crawl4AI.
    """
    
    async def extract_static(self, url: str) -> str:
        """Extract content using fast httpx (best for APIs or static HTML)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            return response.text
            
    async def extract_dynamic(self, url: str) -> str:
        """Extract content using Playwright (best for SPAs/JS-heavy sites)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Anti-detection bypass (basic)
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
            
    async def extract_semantic(self, url: str) -> str:
        """Extract content using Crawl4AI (best for converting to Markdown for LLMs)"""
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
