"use client";
import React from "react";
import { Message } from "@/lib/types";
interface MessageBubbleProps {
    message: Message;
}
export default function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === "user";
    /**
     * Render simple markdown-like formatting:
     * **bold**, `code`, and newlines.
     */
    const renderContent = (text: string) => {
        const parts: React.ReactNode[] = [];
        // Split by **bold**, `code`, and newlines
        const regex = /(\*\*[^*]+\*\*|`[^`]+`|\n)/g;
        let lastIndex = 0;
        let match: RegExpExecArray | null;
        let key = 0;
        while ((match = regex.exec(text)) !== null) {
            // Add text before the match
            if (match.index > lastIndex) {
                parts.push(text.slice(lastIndex, match.index));
            }
            const token = match[0];
            if (token.startsWith("**") && token.endsWith("**")) {
                parts.push(
                    <strong key={key++}>{token.slice(2, -2)}</strong>
                );
            } else if (token.startsWith("`") && token.endsWith("`")) {
                parts.push(
                    <code key={key++}>{token.slice(1, -1)}</code>
                );
            } else if (token === "\n") {
                parts.push(<br key={key++} />);
            }
            lastIndex = match.index + token.length;
        }
        if (lastIndex < text.length) {
            parts.push(text.slice(lastIndex));
        }
        return parts;
    };
    return (
        <div className={`message ${isUser ? "user" : "assistant"}`} id={`msg-${message.id}`}>
            <div className="message-avatar">
                {isUser ? "👤" : "🤖"}
            </div>
            <div className="message-content">
                {renderContent(message.content)}
            </div>
        </div>
    );
}
