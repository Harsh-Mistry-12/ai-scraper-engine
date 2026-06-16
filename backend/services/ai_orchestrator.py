import os
from google import genai
from pydantic import BaseModel
from config import settings

class AIOrchestrator:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        # Use gemini-2.5-flash as the default model
        self.model = 'gemini-2.5-flash'

    async def analyze_intent(self, user_prompt: str) -> dict:
        """
        Extract intent, target URLs, and desired data fields from the user prompt.
        """
        if not self.client:
            return {"error": "GEMINI_API_KEY is not set"}
            
        system_instruction = '''
        You are an AI web scraping assistant. The user will provide a prompt describing what they want to scrape.
        Extract the following information:
        1. target_urls: A list of URLs mentioned in the prompt (if any).
        2. fields_to_extract: A list of specific data fields the user wants.
        3. intent: A brief summary of what they are trying to achieve.
        Output as JSON.
        '''

        try:
            # Note: We are using a simple generation call. Pydantic structured output is preferred
            # but we'll return raw JSON string to be parsed for now.
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                ),
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}

    async def plan_strategy(self, analysis_result: dict, prompt: str) -> str:
        """
        Plan the scraping strategy based on website analysis and user prompt.
        """
        pass
