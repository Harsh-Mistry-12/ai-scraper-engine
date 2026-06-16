/* ── Type definitions for AI Scraper Engine ─────────────────────────── */
export interface Session {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}
export interface Message {
    id: string;
    session_id: string;
    role: "user" | "assistant" | "system";
    content: string;
    message_type: "text" | "pipeline" | "preview" | "error" | "analysis" | "export";
    metadata: Record<string, any>;
    created_at: string;
}
export interface DataPreview {
    columns: string[];
    rows: Record<string, any>[];
    total_rows: number;
    preview_rows: number;
}
export interface PipelineStep {
    name: string;
    status: "pending" | "running" | "completed" | "error";
    detail: string;
    progress?: number;
}
export interface FileUploadResponse {
    id: string;
    original_name: string;
    file_type: string;
    file_size: string;
}
export interface ValidationResult {
    is_valid: boolean;
    quality_score: number;
    issues: string[];
    suggestions: string[];
    summary: string;
}
export interface SSEEvent {
    event: string;
    data: Record<string, any>;
}
// Pipeline steps configuration
export const PIPELINE_STEPS = [
    { key: "understanding", name: "Understanding Request", icon: "🧠" },
    { key: "analyzing", name: "Analyzing Website", icon: "🔍" },
    { key: "planning", name: "Planning Strategy", icon: "📋" },
    { key: "scraping", name: "Scraping Data", icon: "⛏️" },
    { key: "transforming", name: "Transforming Data", icon: "✨" },
] as const;
export type PipelineStepKey = (typeof PIPELINE_STEPS)[number]["key"];
