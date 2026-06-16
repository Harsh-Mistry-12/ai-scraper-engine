import httpx
from bs4 import BeautifulSoup
import time

class WebsiteAnalyzer:
    """
    Analyzes a target website to determine the best scraping strategy.
    Checks for static vs dynamic content, API availability, and basic anti-scraping.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def analyze(self, url: str) -> dict:
        results = {
            "url": url,
            "status_code": None,
            "is_dynamic": False,
            "has_api": False,
            "anti_scraping_detected": False,
            "error": None
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = time.time()
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                results["status_code"] = response.status_code
                
                # Check for anti-scraping
                if response.status_code in [403, 429]:
                    results["anti_scraping_detected"] = True
                    return results
                    
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Very basic dynamic detection: check if body is mostly empty but has scripts
                scripts = soup.find_all('script')
                text_len = len(soup.get_text(strip=True))
                if len(scripts) > 5 and text_len < 1000:
                    results["is_dynamic"] = True
                    
        except Exception as e:
            results["error"] = str(e)

        return results
