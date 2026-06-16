"use client";
import { useState, useRef, useCallback } from "react";
import { FileUploadResponse } from "@/lib/types";
import { uploadFile } from "@/lib/api";
interface MessageInputProps {
    sessionId: string | null;
    onSend: (content: string, fileIds: string[]) => void;
    disabled?: boolean;
}
export default function MessageInput({
    sessionId,
    onSend,
    disabled = false,
}: MessageInputProps) {
    const [text, setText] = useState("");
    const [files, setFiles] = useState<FileUploadResponse[]>([]);
    const [uploading, setUploading] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const handleSend = useCallback(() => {
        const trimmed = text.trim();
        if (!trimmed && files.length === 0) return;
        if (disabled) return;
        onSend(trimmed, files.map((f) => f.id));
        setText("");
        setFiles([]);
        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = "40px";
        }
    }, [text, files, disabled, onSend]);
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(e.target.value);
        // Auto-resize textarea
        const ta = e.target;
        ta.style.height = "40px";
        ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    };
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = e.target.files;
        if (!selectedFiles || !sessionId) return;
        setUploading(true);
        try {
            for (const file of Array.from(selectedFiles)) {
                const result = await uploadFile(sessionId, file);
                setFiles((prev) => [...prev, result]);
            }
        } catch (err) {
            console.error("Upload failed:", err);
        } finally {
            setUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };
    const removeFile = (id: string) => {
        setFiles((prev) => prev.filter((f) => f.id !== id));
    };
    return (
        <div className="input-area" id="input-area">
            {/* File chips */}
            {files.length > 0 && (
                <div style={{ maxWidth: 800, margin: "0 auto 8px" }}>
                    {files.map((f) => (
                        <span key={f.id} className="file-chip">
                            <span className="file-chip-icon">📎</span>
                            {f.original_name}
                            <span
                                className="file-chip-remove"
                                onClick={() => removeFile(f.id)}
                            >
                                ✕
                            </span>
                        </span>
                    ))}
                </div>
            )}
            <div className="input-bar">
                {/* Upload button */}
                <button
                    className="input-upload-btn"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={!sessionId || uploading}
                    title="Upload file (CSV, XLSX, JSON, XML)"
                    id="upload-btn"
                >
                    {uploading ? "⏳" : "📎"}
                </button>
                <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden-input"
                    accept=".csv,.xlsx,.json,.xml"
                    onChange={handleFileSelect}
                    multiple
                />
                {/* Text input */}
                <textarea
                    ref={textareaRef}
                    className="input-textarea"
                    placeholder={
                        sessionId
                            ? "Describe what you want to scrape..."
                            : "Create a new chat to start..."
                    }
                    value={text}
                    onChange={handleTextChange}
                    onKeyDown={handleKeyDown}
                    disabled={!sessionId || disabled}
                    rows={1}
                    id="message-input"
                />
                {/* Send button */}
                <button
                    className="input-send-btn"
                    onClick={handleSend}
                    disabled={!sessionId || disabled || (!text.trim() && files.length === 0)}
                    title="Send message"
                    id="send-btn"
                >
                    ➤
                </button>
            </div>
        </div>
    );
}
