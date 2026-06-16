from services.website_analyzer import WebsiteAnalyzer
from services.ai_orchestrator import AIOrchestrator
import asyncio

class ScrapingPipeline:
    def __init__(self):
        self.analyzer = WebsiteAnalyzer()
        self.orchestrator = AIOrchestrator()

    async def run_pipeline(self, prompt: str, session_id: str, websocket=None):
        """
        Runs the full scraping pipeline.
        If websocket is provided, it streams progress updates.
        """
        async def send_update(stage: str, message: str, data: dict = None):
            if websocket:
                await websocket.send_json({
                    "type": "progress",
                    "stage": stage,
                    "content": message,
                    "data": data or {}
                })

        # Stage 1: Analyze Intent
        await send_update("intent", "Analyzing your request with AI...")
        intent_data = await self.orchestrator.analyze_intent(prompt)
        
        if "error" in intent_data:
            await send_update("error", f"AI Error: {intent_data['error']}")
            return
            
        urls = intent_data.get("target_urls", [])
        if not urls:
            await send_update("error", "No target URLs found in your request.")
            return

        target_url = urls[0]
        
        # Stage 2: Analyze Website
        await send_update("analysis", f"Analyzing website: {target_url}...")
        analysis_result = await self.analyzer.analyze(target_url)
        
        if analysis_result.get("error") or analysis_result.get("status_code") not in [200, 201]:
            await send_update("error", f"Failed to access {target_url}. It might have strong anti-scraping measures.")
            return
            
        # Stage 3: Strategy & Execution
        # This is a stub for the actual extraction logic which will use Playwright/Crawl4AI
        strategy = "dynamic" if analysis_result.get("is_dynamic") else "static"
        await send_update("strategy", f"Decided on {strategy} scraping strategy.")
        
        await send_update("executing", f"Executing scraping using {strategy} approach...")
        await asyncio.sleep(2) # Simulate scraping time
        
        # Mock extracted data
        mock_data = [
            {"id": 1, "field1": "Sample Data 1", "field2": "More info"},
            {"id": 2, "field1": "Sample Data 2", "field2": "More info"}
        ]
        
        await send_update("preview", "Scraping complete. Preparing preview.", {"preview_data": mock_data})
        
        return mock_data
