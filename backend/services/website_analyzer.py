"""Website analyzer — visits a URL, detects content type, APIs, and anti-scraping measures."""
from __future__ import annotations
import logging
import re
from urllib.parse import urljoin, urlparse
from typing import Any
import httpx
from bs4 import BeautifulSoup
from utils.anti_detection import get_default_headers, check_robots_txt
logger = logging.getLogger(__name__)
class WebsiteAnalyzer:
    """Performs reconnaissance on a target website before scraping."""
    async def analyze(self, url: str) -> dict[str, Any]:
        """
        Full website analysis following the README checklist:
        1. Visit the website
        2. Detect static vs dynamic content
        3. Check for available APIs
        4. Detect anti-scraping measures
        5. Recommend scraping technique
        """
        result = {
            "url": url,
            "is_dynamic": False,
            "has_api": False,
            "api_details": None,
            "anti_scraping": [],
            "recommended_technique": "direct_http",
            "robots_txt": None,
            "page_title": "",
            "content_type": "",
            "html_sample": "",
            "notes": [],
        }
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        async with httpx.AsyncClient(
            headers=get_default_headers(),
            follow_redirects=True,
            timeout=30.0,
            verify=False,
        ) as client:
            # ── Step 1: Fetch the page ───────────────────────────────
            try:
                response = await client.get(url)
                html = response.text
                result["content_type"] = response.headers.get("content-type", "")
                result["html_sample"] = self._clean_html_sample(html)  # Store cleaned HTML for AI analysis
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                result["notes"].append(f"Failed to fetch page: {str(e)[:200]}")
                result["recommended_technique"] = "browser_automation"
                return result
            # ── Step 2: Parse and analyze ─────────────────────────────
            soup = BeautifulSoup(html, "html.parser")
            result["page_title"] = soup.title.string.strip() if soup.title and soup.title.string else ""
            # Detect dynamic content indicators
            dynamic_indicators = self._detect_dynamic_content(html, soup)
            result["is_dynamic"] = len(dynamic_indicators) > 0
            if dynamic_indicators:
                result["notes"].append(f"Dynamic content detected: {', '.join(dynamic_indicators)}")
            # ── Step 3: Check for APIs ────────────────────────────────
            api_info = self._detect_apis(html, soup, base_url)
            if api_info:
                result["has_api"] = True
                result["api_details"] = api_info
                result["notes"].append("API endpoints detected in page source")
            # ── Step 4: Anti-scraping detection ───────────────────────
            anti_scraping = self._detect_anti_scraping(html, soup, response.headers)
            result["anti_scraping"] = anti_scraping
            # ── Step 5: Check robots.txt ──────────────────────────────
            try:
                robots_resp = await client.get(f"{base_url}/robots.txt")
                if robots_resp.status_code == 200:
                    result["robots_txt"] = robots_resp.text[:2000]
                    is_allowed = check_robots_txt(robots_resp.text, parsed.path or "/")
                    if not is_allowed:
                        result["notes"].append("⚠️ robots.txt disallows scraping this path")
                        result["anti_scraping"].append("robots_txt_disallow")
            except Exception:
                result["notes"].append("Could not fetch robots.txt")
            # ── Step 6: Recommend technique ───────────────────────────
            result["recommended_technique"] = self._recommend_technique(result)
        return result
    def _detect_dynamic_content(self, html: str, soup: BeautifulSoup) -> list[str]:
        """Check if the page loads content dynamically via JavaScript."""
        indicators = []
        # Check for JS frameworks
        frameworks = {
            "react": [r"__NEXT_DATA__", r"_reactRoot", r"react-root"],
            "angular": [r"ng-app", r"ng-controller", r"angular"],
            "vue": [r"__vue__", r"v-app", r"vue-app"],
            "svelte": [r"svelte"],
        }
        for framework, patterns in frameworks.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    indicators.append(f"{framework}_framework")
                    break
        # Check for AJAX/fetch patterns
        if re.search(r"fetch\s*\(|XMLHttpRequest|axios\.|\.ajax\s*\(", html):
            indicators.append("ajax_data_loading")
        # Check for lazy loading
        if soup.find_all(attrs={"data-src": True}) or soup.find_all("img", {"loading": "lazy"}):
            indicators.append("lazy_loading")
        # Check for empty content containers (data loaded via JS)
        empty_containers = soup.find_all(["div", "section"], id=True)
        empty_count = sum(1 for c in empty_containers if len(c.get_text(strip=True)) == 0 and len(c.find_all()) < 2)
        if empty_count > 3:
            indicators.append("empty_js_containers")
        return indicators
    def _detect_apis(self, html: str, soup: BeautifulSoup, base_url: str) -> dict[str, Any] | None:
        """Try to discover API endpoints from the page source."""
        api_endpoints = set()
        api_info: dict[str, Any] = {"endpoints": [], "type": "unknown"}
        # Look for API URLs in JavaScript
        api_patterns = [
            r'["\'](?:https?://[^"\']*?/api/[^"\']*)["\']',
            r'["\'](?:/api/[^"\']*)["\']',
            r'["\'](?:https?://[^"\']*?/graphql)["\']',
            r'["\'](?:/graphql)["\']',
            r'["\'](?:https?://[^"\']*?/v\d+/[^"\']*)["\']',
        ]
        for pattern in api_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                endpoint = match.strip("\"'")
                api_endpoints.add(endpoint)
        # Check for GraphQL
        if any("graphql" in ep.lower() for ep in api_endpoints):
            api_info["type"] = "graphql"
        # Check for REST patterns
        elif any("/api/" in ep or re.search(r"/v\d+/", ep) for ep in api_endpoints):
            api_info["type"] = "rest"
        if api_endpoints:
            api_info["endpoints"] = list(api_endpoints)[:20]  # Limit to 20
            return api_info
        return None
    def _detect_anti_scraping(self, html: str, soup: BeautifulSoup, headers: dict) -> list[str]:
        """Detect anti-scraping measures on the page."""
        measures = []
        # CAPTCHA detection
        captcha_patterns = [
            (r"recaptcha", "recaptcha"),
            (r"hcaptcha", "hcaptcha"),
            (r"captcha", "generic_captcha"),
            (r"cf-turnstile", "cloudflare_turnstile"),
        ]
        for pattern, name in captcha_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                measures.append(name)
                break
        # Cloudflare detection
        if "cf-ray" in str(headers).lower() or "cloudflare" in str(headers).lower():
            measures.append("cloudflare")
        if re.search(r"challenge-platform|jschl_vc|jschl_answer", html):
            measures.append("cloudflare_challenge")
        # Rate limiting headers
        rate_headers = ["x-ratelimit-limit", "x-ratelimit-remaining", "retry-after"]
        for h in rate_headers:
            if h in {k.lower() for k in headers.keys()}:
                measures.append("rate_limiting")
                break
        # Session/cookie requirements
        if "set-cookie" in {k.lower() for k in headers.keys()}:
            measures.append("session_cookies")
        # CSP headers that might block scraping
        csp = headers.get("content-security-policy", "")
        if csp:
            measures.append("content_security_policy")
        return measures
    def _recommend_technique(self, analysis: dict) -> str:
        """Based on analysis, recommend the best scraping technique."""
        anti = analysis.get("anti_scraping", [])
        has_api = analysis.get("has_api", False)
        is_dynamic = analysis.get("is_dynamic", False)
        # If clean API available, use it
        if has_api and not any(m in anti for m in ["cloudflare", "recaptcha"]):
            return "api_integration"
        # If heavy anti-scraping or dynamic content, use browser
        heavy_protection = {"cloudflare_challenge", "recaptcha", "hcaptcha", "cloudflare_turnstile"}
        if heavy_protection.intersection(anti) or is_dynamic:
            return "browser_automation"
        # Default to direct HTTP (fastest)
        return "direct_http"

    def _clean_html_sample(self, html: str) -> str:
        """Strip scripts, styles, metas, and SVGs to provide a dense content-rich HTML structure to the AI."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remove heavy non-content nodes
            for element in soup(["script", "style", "meta", "link", "svg", "path", "iframe", "noscript"]):
                element.decompose()
            body = soup.body if soup.body else soup
            # Prettify and remove excessive whitespace/blank lines
            text = body.prettify()
            lines = [line for line in text.splitlines() if line.strip()]
            return "\n".join(lines)[:12000]
        except Exception:
            return html[:10000]
