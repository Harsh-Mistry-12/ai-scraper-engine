"""AI service wrapping the Google Gemini API for prompt understanding and strategy planning.
Includes retry with exponential backoff and automatic fallback to alternative
models when the primary model returns 503 / 429 / UNAVAILABLE errors.
"""
from __future__ import annotations
import asyncio
import json
import logging
import random
from typing import Any
from google import genai
from google.genai import types
import config
logger = logging.getLogger(__name__)
# HTTP status codes / error substrings that indicate a transient overload
_RETRYABLE_INDICATORS = ("503", "429", "unavailable", "overloaded", "resource_exhausted", "rate limit", "quota")
def _is_retryable(error: Exception) -> bool:
    """Return True if the error looks like a transient capacity issue."""
    msg = str(error).lower()
    return any(indicator in msg for indicator in _RETRYABLE_INDICATORS)
class AIService:
    """Handles all interactions with the Gemini API with built-in resilience."""
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.primary_model = config.GEMINI_MODEL
        self.fallback_models = [m.strip() for m in config.GEMINI_FALLBACK_MODELS if m.strip()]
        self.max_retries = config.AI_MAX_RETRIES
        self.base_delay = config.AI_RETRY_BASE_DELAY
    # ── Core call with retry + fallback ──────────────────────────────────
    async def _call_gemini(
        self,
        contents: list[types.Content],
        gen_config: types.GenerateContentConfig,
        *,
        label: str = "AI call",
    ) -> str:
        """
        Call the Gemini API with automatic retry and model fallback.
        Strategy:
        1. Try the primary model up to `max_retries` times with exponential backoff.
        2. If all retries fail with a retryable error, try each fallback model once.
        3. If everything fails, raise the last exception.
        Returns the response text.
        """
        models_to_try = [self.primary_model] + self.fallback_models
        last_exception: Exception | None = None
        for model_idx, model_name in enumerate(models_to_try):
            is_primary = model_idx == 0
            retries = self.max_retries if is_primary else 1  # Full retries only for primary
            for attempt in range(1, retries + 1):
                try:
                    logger.info(
                        f"[{label}] Calling model={model_name} (attempt {attempt}/{retries})"
                    )
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=gen_config,
                    )
                    if model_idx > 0:
                        logger.info(
                            f"[{label}] ✅ Fallback model '{model_name}' succeeded"
                        )
                    return response.text
                except Exception as e:
                    last_exception = e
                    if _is_retryable(e):
                        # Calculate delay with jitter: base * 2^attempt + random jitter
                        delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        logger.warning(
                            f"[{label}] ⚠️ Retryable error on {model_name} "
                            f"(attempt {attempt}/{retries}): {str(e)[:150]}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        # Non-retryable error — don't retry, don't fallback
                        logger.error(
                            f"[{label}] ❌ Non-retryable error on {model_name}: {str(e)[:300]}"
                        )
                        raise
            # Exhausted retries for this model — try next fallback
            if is_primary:
                logger.warning(
                    f"[{label}] Primary model '{model_name}' exhausted all {retries} retries. "
                    f"Trying fallback models: {self.fallback_models}"
                )
            else:
                logger.warning(
                    f"[{label}] Fallback model '{model_name}' failed. Moving to next."
                )
        # All models exhausted
        raise last_exception or RuntimeError("All models failed with no captured exception")
    # ── Helper to build a safe JSON response ─────────────────────────────
    def _safe_parse_json(self, text: str, fallback: dict) -> dict:
        """Parse JSON from AI response, returning fallback on failure."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse AI JSON response: {e}. Raw: {text[:200]}")
            return fallback
    # ── Public Methods ───────────────────────────────────────────────────
    async def understand_prompt(
        self,
        user_message: str,
        conversation_history: list[dict],
        file_schema: dict | None = None,
        session_context: dict | None = None,
    ) -> dict[str, Any]:
        """
        Analyze the user's message and extract structured intent.
        Returns a dict with:
        - intent: 'scrape' | 'question' | 'modify' | 'approve' | 'clarify'
        - target_url: str or None
        - desired_fields: list[str]
        - output_format: str or None
        - input_file_mapping: dict or None (how input file columns map to scraping)
        - follow_up_question: str or None (if we need more info)
        - response_text: str (natural language response to user)
        """
        system_prompt = """You are an AI assistant that helps users scrape data from websites. 
Your job is to understand what the user wants and extract structured information from their request.
Analyze the user's message and return a JSON object with these fields:
{
    "intent": "scrape" | "question" | "modify" | "approve" | "clarify",
    "target_url": "the URL to scrape, or null",
    "desired_fields": ["list", "of", "fields", "to", "extract"],
    "output_format": "csv" | "xlsx" | "json" | "xml" | null,
    "input_file_mapping": {"column_name": "description of how to use it"} or null,
    "follow_up_question": "question to ask if info is missing, or null",
    "response_text": "natural language response to show the user"
}
Rules:
- If the user hasn't specified a URL, ask for it in follow_up_question
- If the user hasn't specified what fields to extract, try to infer from context or ask
- If they uploaded a file, consider how each column relates to the scraping task
- Be conversational and helpful in response_text
- If the user is just asking a question (not requesting scraping), set intent to "question"
- If the user says "approve", "looks good", "yes", etc., set intent to "approve"
"""
        messages = []
        # Add conversation history for context
        for msg in conversation_history[-10:]:
            messages.append(
                types.Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        # Build the current prompt with file context
        current_prompt = user_message
        if file_schema:
            current_prompt += f"\n\n[User uploaded a file with this schema: {json.dumps(file_schema)}]"
        if session_context:
            current_prompt += f"\n\n[Current session context: {json.dumps(session_context)}]"
        messages.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=current_prompt)]
            )
        )
        error_fallback = {
            "intent": "question",
            "target_url": None,
            "desired_fields": [],
            "output_format": None,
            "input_file_mapping": None,
            "follow_up_question": None,
            "response_text": "",
        }
        try:
            text = await self._call_gemini(
                contents=messages,
                gen_config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
                label="understand_prompt",
            )
            return self._safe_parse_json(text, {
                **error_fallback,
                "response_text": text,  # If JSON parse fails, show raw response
            })
        except Exception as e:
            logger.error(f"AI prompt understanding failed after all retries: {e}")
            return {
                **error_fallback,
                "response_text": (
                    f"⚠️ The AI service is temporarily unavailable (all models tried). "
                    f"Please wait a moment and try again.\n\n"
                    f"**Error**: {str(e)[:200]}"
                ),
            }
    async def plan_scraping_strategy(
        self,
        target_url: str,
        desired_fields: list[str],
        website_analysis: dict,
        page_html_sample: str = "",
    ) -> dict[str, Any]:
        """
        Given website analysis results, plan the optimal scraping strategy.
        Returns CSS selectors, pagination logic, and technique recommendation.
        """
        system_prompt = """You are a web scraping expert. Given a website analysis and desired data fields,
create a detailed scraping plan.
Return a JSON object:
{
    "technique": "direct_http" | "browser_automation" | "api_integration",
    "selectors": {
        "field_name": "CSS selector or XPath",
        ...
    },
    "container_selector": "CSS selector for the repeating container element",
    "pagination": {
        "type": "none" | "next_button" | "url_parameter" | "infinite_scroll",
        "selector": "CSS selector for next button or null",
        "url_pattern": "URL pattern with {page} placeholder or null",
        "max_pages": 10
    },
    "wait_for_selector": "CSS selector to wait for before scraping (for dynamic sites)",
    "notes": ["any special considerations"],
    "code_snippet": "optional Python code snippet for complex extraction logic"
}
Guidelines:
- Prefer direct HTTP when possible (faster, lighter)
- Use browser automation only for JS-heavy dynamic sites
- Use API integration if a clean API was discovered
- Generate precise, specific selectors
- Consider anti-scraping measures from the analysis
"""
        prompt = f"""
Target URL: {target_url}
Desired fields to extract: {json.dumps(desired_fields)}
Website analysis: {json.dumps(website_analysis)}
Sample HTML (first 12000 chars):
{page_html_sample[:12000]}"""
        error_fallback = {
            "technique": "browser_automation",
            "selectors": {},
            "container_selector": "",
            "pagination": {"type": "none"},
            "notes": [],
        }
        try:
            text = await self._call_gemini(
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                gen_config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
                label="plan_strategy",
            )
            return self._safe_parse_json(text, {
                **error_fallback,
                "notes": [f"Used raw response (JSON parse failed): {text[:200]}"],
            })
        except Exception as e:
            logger.error(f"AI strategy planning failed after all retries: {e}")
            return {
                **error_fallback,
                "notes": [f"AI planning unavailable, using browser fallback: {str(e)[:150]}"],
            }
    async def generate_session_title(self, first_message: str) -> str:
        """Generate a short, descriptive title for a chat session."""
        try:
            text = await self._call_gemini(
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(
                            text=f'Generate a very short title (3-6 words) for a scraping session that started with this message: "{first_message}". Return ONLY the title text, nothing else.'
                        )]
                    )
                ],
                gen_config=types.GenerateContentConfig(temperature=0.5),
                label="session_title",
            )
            title = text.strip().strip('"').strip("'")
            return title[:60]
        except Exception:
            # Title generation is non-critical — just truncate the message
            return first_message[:40] + "..." if len(first_message) > 40 else first_message
    async def validate_scraped_data(
        self,
        desired_fields: list[str],
        sample_data: list[dict],
        user_instructions: str,
    ) -> dict[str, Any]:
        """Validate that scraped data matches user's requirements."""
        system_prompt = """You are a data quality validator. Check if the scraped data matches what the user asked for.
Return JSON:
{
    "is_valid": true/false,
    "quality_score": 0-100,
    "issues": ["list of issues found"],
    "suggestions": ["list of suggestions"],
    "summary": "brief summary of data quality"
}"""
        prompt = f"""
User wanted these fields: {json.dumps(desired_fields)}
User's original instruction: {user_instructions}
Sample of scraped data (first 5 rows):
{json.dumps(sample_data[:5], indent=2)}
"""
        error_fallback = {
            "is_valid": True,
            "quality_score": 50,
            "issues": [],
            "suggestions": [],
            "summary": "Validation skipped — AI service unavailable.",
        }
        try:
            text = await self._call_gemini(
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                gen_config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
                label="validate_data",
            )
            return self._safe_parse_json(text, error_fallback)
        except Exception as e:
            logger.error(f"AI validation failed after all retries: {e}")
            return {
                **error_fallback,
                "issues": [f"Validation unavailable: {str(e)[:100]}"],
            }
