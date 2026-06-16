"""Chat service — orchestrates the full AI scraping pipeline per user message."""
from __future__ import annotations
import json
import logging
from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from services.ai_service import AIService
from services.website_analyzer import WebsiteAnalyzer
from services.scraping_engine import ScrapingEngine
from services.data_transformer import DataTransformer
from services.session_store import SessionStore
from utils.file_handler import read_file_to_df, get_file_schema
logger = logging.getLogger(__name__)
class ChatService:
    """
    Main orchestrator for the chat-based scraping pipeline.
    Flow:
    1. User sends message → AI understands intent
    2. If scrape intent → analyze website → plan strategy → execute → preview
    3. If approve → export final data
    4. If question → AI responds directly
    """
    def __init__(self, db: AsyncSession):
        self.store = SessionStore(db)
        self.ai = AIService()
        self.analyzer = WebsiteAnalyzer()
        self.scraper = ScrapingEngine()
        self.transformer = DataTransformer()
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        file_ids: list[str] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Process a user message and yield SSE events.
        Yields dicts with:
        - event: 'message' | 'pipeline_update' | 'preview' | 'error' | 'complete' | 'export'
        - data: event payload
        """
        # Save user message
        await self.store.add_message(session_id, "user", user_message)
        # Get session context and history
        session = await self.store.get_session(session_id)
        if not session:
            yield {"event": "error", "data": {"message": "Session not found"}}
            return
        context = session.context or {}
        history = await self.store.get_conversation_context(session_id)
        # Get file schema if files were uploaded
        file_schema = None
        if file_ids:
            files = await self.store.get_files(session_id)
            for f in files:
                if f.id in file_ids:
                    try:
                        df = read_file_to_df(f.stored_path)
                        file_schema = get_file_schema(df)
                        context["input_file"] = {
                            "id": f.id,
                            "name": f.original_name,
                            "path": f.stored_path,
                            "schema": file_schema,
                        }
                    except Exception as e:
                        logger.error(f"Failed to read file {f.original_name}: {e}")
        # ── Stage 1: AI Understanding ────────────────────────────────
        yield {
            "event": "pipeline_update",
            "data": {"step": "understanding", "status": "running", "detail": "Understanding your request..."},
        }
        understanding = await self.ai.understand_prompt(user_message, history, file_schema, context)
        # Generate title for new sessions
        if len(history) <= 2:
            title = await self.ai.generate_session_title(user_message)
            await self.store.update_session_title(session_id, title)
        yield {
            "event": "pipeline_update",
            "data": {"step": "understanding", "status": "completed", "detail": "Request analyzed"},
        }
        intent = understanding.get("intent", "question")
        # ── Handle different intents ─────────────────────────────────
        if intent == "question":
            response_text = understanding.get("response_text", "I can help you with web scraping. What would you like to scrape?")
            await self.store.add_message(session_id, "assistant", response_text)
            yield {"event": "message", "data": {"content": response_text, "role": "assistant"}}
            return
        if intent == "clarify" or understanding.get("follow_up_question"):
            response_text = understanding.get("response_text", understanding.get("follow_up_question", ""))
            await self.store.add_message(session_id, "assistant", response_text)
            yield {"event": "message", "data": {"content": response_text, "role": "assistant"}}
            return
        if intent == "approve":
            # Export the previewed data
            async for event in self._handle_approve(session_id, context):
                yield event
            return
        if intent == "scrape":
            # Update context with extracted info
            target_url = understanding.get("target_url", context.get("target_url"))
            desired_fields = understanding.get("desired_fields", context.get("desired_fields", []))
            output_format = understanding.get("output_format", context.get("output_format", "csv"))
            if not target_url:
                msg = understanding.get("response_text", "I need a URL to scrape. Could you provide the website URL?")
                await self.store.add_message(session_id, "assistant", msg)
                yield {"event": "message", "data": {"content": msg, "role": "assistant"}}
                return
            context.update({
                "target_url": target_url,
                "desired_fields": desired_fields,
                "output_format": output_format,
                "input_file_mapping": understanding.get("input_file_mapping"),
            })
            await self.store.update_session_context(session_id, context)
            # Tell user what we understood
            msg = understanding.get("response_text", f"Got it! I'll scrape {target_url} for you.")
            await self.store.add_message(session_id, "assistant", msg)
            yield {"event": "message", "data": {"content": msg, "role": "assistant"}}
            # ── Stage 2: Website Analysis ─────────────────────────
            yield {
                "event": "pipeline_update",
                "data": {"step": "analyzing", "status": "running", "detail": f"Analyzing {target_url}..."},
            }
            analysis = await self.analyzer.analyze(target_url)
            context["website_analysis"] = {
                k: v for k, v in analysis.items() if k != "html_sample"
            }
            await self.store.update_session_context(session_id, context)
            analysis_summary = self._format_analysis(analysis)
            await self.store.add_message(session_id, "assistant", analysis_summary, message_type="analysis")
            yield {
                "event": "pipeline_update",
                "data": {"step": "analyzing", "status": "completed", "detail": "Website analyzed"},
            }
            yield {"event": "message", "data": {"content": analysis_summary, "role": "assistant"}}
            # ── Stage 3: Strategy Planning ────────────────────────
            yield {
                "event": "pipeline_update",
                "data": {"step": "planning", "status": "running", "detail": "Planning scraping strategy..."},
            }
            strategy = await self.ai.plan_scraping_strategy(
                target_url, desired_fields, analysis, analysis.get("html_sample", "")
            )
            context["scraping_strategy"] = strategy
            await self.store.update_session_context(session_id, context)
            yield {
                "event": "pipeline_update",
                "data": {
                    "step": "planning",
                    "status": "completed",
                    "detail": f"Using {strategy.get('technique', 'unknown')} technique",
                },
            }
            # ── Stage 4: Scraping ─────────────────────────────────
            yield {
                "event": "pipeline_update",
                "data": {"step": "scraping", "status": "running", "detail": "Starting data extraction..."},
            }
            scraped_data = []
            async for update in self.scraper.scrape(strategy, target_url):
                if update["type"] == "progress":
                    yield {
                        "event": "pipeline_update",
                        "data": {
                            "step": "scraping",
                            "status": "running",
                            "detail": update["detail"],
                            "progress": update.get("progress"),
                        },
                    }
                elif update["type"] == "data":
                    scraped_data = update["data"]
                elif update["type"] == "error":
                    yield {
                        "event": "pipeline_update",
                        "data": {"step": "scraping", "status": "error", "detail": update["detail"]},
                    }
                    error_msg = f"⚠️ Scraping encountered an issue: {update['detail']}"
                    await self.store.add_message(session_id, "assistant", error_msg, message_type="error")
                    yield {"event": "message", "data": {"content": error_msg, "role": "assistant"}}
                    return
                elif update["type"] == "complete":
                    yield {
                        "event": "pipeline_update",
                        "data": {"step": "scraping", "status": "completed", "detail": update["detail"]},
                    }
            if not scraped_data:
                error_msg = "❌ No data was scraped. Would you like me to try a different approach?"
                await self.store.add_message(session_id, "assistant", error_msg, message_type="error")
                yield {"event": "message", "data": {"content": error_msg, "role": "assistant"}}
                return
            # ── Stage 5: Transform & Preview ──────────────────────
            yield {
                "event": "pipeline_update",
                "data": {"step": "transforming", "status": "running", "detail": "Transforming data..."},
            }
            df = self.transformer.transform(scraped_data, desired_fields)
            preview = self.transformer.get_preview(df)
            # Store for later export
            context["scraped_data_path"] = str(
                self.transformer.export(df, session_id, "csv", f"_temp_{session_id[:8]}.csv")
            )
            context["total_rows"] = len(df)
            await self.store.update_session_context(session_id, context)
            yield {
                "event": "pipeline_update",
                "data": {"step": "transforming", "status": "completed", "detail": f"Transformed {len(df)} rows"},
            }
            # ── Stage 6: Validate with AI ─────────────────────────
            validation = await self.ai.validate_scraped_data(
                desired_fields, preview["rows"][:5], user_message
            )
            preview_msg = (
                f"✅ Scraped **{preview['total_rows']}** rows with **{len(preview['columns'])}** columns.\n\n"
                f"**Quality Score**: {validation.get('quality_score', 'N/A')}/100\n\n"
                f"{validation.get('summary', '')}\n\n"
                "Here's a preview of the data. Would you like to **approve** and download, or should I **retry** with adjustments?"
            )
            await self.store.add_message(session_id, "assistant", preview_msg, message_type="preview",
                                         metadata={"preview": preview, "validation": validation})
            yield {"event": "preview", "data": {"preview": preview, "validation": validation, "message": preview_msg}}
            return
    async def _handle_approve(
        self,
        session_id: str,
        context: dict,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Handle user approval — export the final data."""
        temp_path = context.get("scraped_data_path")
        output_format = context.get("output_format", "csv")
        if not temp_path:
            msg = "❌ No data to export. Please run a scraping task first."
            await self.store.add_message(session_id, "assistant", msg)
            yield {"event": "message", "data": {"content": msg, "role": "assistant"}}
            return
        try:
            df = read_file_to_df(temp_path, "csv")
            filename = f"scraped_data_{session_id[:8]}.{output_format}"
            export_path = self.transformer.export(df, session_id, output_format, filename)
            msg = f"✅ Data exported successfully as **{filename}**! You can download it now."
            await self.store.add_message(session_id, "assistant", msg, message_type="export",
                                         metadata={"filename": filename, "format": output_format, "rows": len(df)})
            yield {
                "event": "export",
                "data": {
                    "download_url": f"/api/files/download/{filename}",
                    "filename": filename,
                    "format": output_format,
                    "total_rows": len(df),
                    "message": msg,
                },
            }
        except Exception as e:
            msg = f"❌ Export failed: {str(e)[:200]}"
            await self.store.add_message(session_id, "assistant", msg, message_type="error")
            yield {"event": "error", "data": {"message": msg}}
    def _format_analysis(self, analysis: dict) -> str:
        """Format website analysis into a readable message."""
        parts = [f"🔍 **Website Analysis for** `{analysis['url']}`\n"]
        if analysis.get("page_title"):
            parts.append(f"📄 **Title**: {analysis['page_title']}")
        parts.append(f"⚡ **Content Type**: {'Dynamic (JavaScript)' if analysis.get('is_dynamic') else 'Static HTML'}")
        if analysis.get("has_api"):
            api = analysis.get("api_details", {})
            parts.append(f"🔌 **API Detected**: {api.get('type', 'unknown').upper()} ({len(api.get('endpoints', []))} endpoints)")
        technique_labels = {
            "direct_http": "🚀 Direct HTTP (fastest)",
            "browser_automation": "🌐 Browser Automation (for dynamic content)",
            "api_integration": "🔌 API Integration (cleanest)",
        }
        rec = analysis.get("recommended_technique", "direct_http")
        parts.append(f"🎯 **Recommended Approach**: {technique_labels.get(rec, rec)}")
        anti = analysis.get("anti_scraping", [])
        if anti:
            parts.append(f"🛡️ **Anti-Scraping Detected**: {', '.join(anti)}")
        notes = analysis.get("notes", [])
        if notes:
            parts.append("\n📝 **Notes**:")
            for note in notes:
                parts.append(f"  • {note}")
        return "\n".join(parts)
