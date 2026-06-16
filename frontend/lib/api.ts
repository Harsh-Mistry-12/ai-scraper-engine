/* ── API client for communicating with the FastAPI backend ─────────── */
import type { Session, Message, FileUploadResponse } from "./types";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
/* ── Helper ────────────────────────────────────────────────────────── */
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${url}`, {
        headers: { "Content-Type": "application/json", ...options?.headers },
        ...options,
    });
    if (!response.ok) {
        const error = await response.text();
        throw new Error(`API Error ${response.status}: ${error}`);
    }
    return response.json();
}
/* ── Sessions ──────────────────────────────────────────────────────── */
export async function createSession(title?: string): Promise<Session> {
    return fetchJSON<Session>("/api/sessions/", {
        method: "POST",
        body: JSON.stringify({ title: title || "New Chat" }),
    });
}
export async function listSessions(): Promise<Session[]> {
    const data = await fetchJSON<{ sessions: Session[] }>("/api/sessions/");
    return data.sessions;
}
export async function deleteSession(sessionId: string): Promise<void> {
    await fetchJSON(`/api/sessions/${sessionId}`, { method: "DELETE" });
}
/* ── Messages ──────────────────────────────────────────────────────── */
export async function getChatHistory(sessionId: string): Promise<Message[]> {
    const data = await fetchJSON<{ messages: Message[] }>(
        `/api/chat/${sessionId}/history`
    );
    return data.messages;
}
/**
 * Send a message and receive SSE events.
 * Returns an async generator that yields parsed SSE events.
 */
export async function* sendMessage(
    sessionId: string,
    content: string,
    fileIds: string[] = []
): AsyncGenerator<{ event: string; data: Record<string, any> }> {
    const response = await fetch(
        `${API_BASE}/api/chat/${sessionId}/message`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content, file_ids: fileIds }),
        }
    );
    if (!response.ok) {
        throw new Error(`API Error ${response.status}`);
    }
    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        let currentEvent = "message";
        for (const line of lines) {
            if (line.startsWith("event: ")) {
                currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
                try {
                    const data = JSON.parse(line.slice(6));
                    yield { event: currentEvent, data };
                } catch {
                    // Skip malformed data
                }
            }
        }
    }
}
/* ── Files ─────────────────────────────────────────────────────────── */
export async function uploadFile(
    sessionId: string,
    file: File
): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(
        `${API_BASE}/api/files/upload/${sessionId}`,
        {
            method: "POST",
            body: formData,
        }
    );
    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Upload failed: ${error}`);
    }
    return response.json();
}
export function getDownloadUrl(filename: string): string {
    return `${API_BASE}/api/files/download/${filename}`;
}
/* ── Health ─────────────────────────────────────────────────────────── */
export async function checkHealth(): Promise<{
    status: string;
    gemini_configured: boolean;
}> {
    return fetchJSON("/api/health");
}
