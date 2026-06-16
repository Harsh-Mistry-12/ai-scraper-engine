"use client";
import { useRef, useEffect } from "react";
import { Message, DataPreview as DataPreviewType, ValidationResult } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import PipelineProgress from "./PipelineProgress";
import DataPreview from "./DataPreview";
interface PipelineState {
    [key: string]: {
        status: "pending" | "running" | "completed" | "error";
        detail: string;
        progress?: number;
    };
}
interface ChatAreaProps {
    messages: Message[];
    pipelineState: PipelineState | null;
    previewData: { preview: DataPreviewType; validation?: ValidationResult } | null;
    isLoading: boolean;
    onApprove: (format: string) => void;
    onRetry: () => void;
    onExampleClick: (text: string) => void;
}
export default function ChatArea({
    messages,
    pipelineState,
    previewData,
    isLoading,
    onApprove,
    onRetry,
    onExampleClick,
}: ChatAreaProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, pipelineState, previewData, isLoading]);
    // Show welcome screen if no messages
    if (messages.length === 0 && !isLoading) {
        return (
            <div className="welcome-screen" id="welcome-screen">
                <div className="welcome-icon">⚡</div>
                <h1 className="welcome-title">AI Scraper Engine</h1>
                <p className="welcome-subtitle">
                    Tell me what data you need and I&apos;ll build a scraping pipeline to
                    get it. Upload your input file, provide a URL, and describe your
                    desired output.
                </p>
                <div className="welcome-cards">
                    <div
                        className="welcome-card"
                        onClick={() =>
                            onExampleClick(
                                "Scrape https://news.ycombinator.com and get me the title, URL, and points of all stories on the front page. Output as CSV."
                            )
                        }
                    >
                        <div className="welcome-card-icon">📰</div>
                        <div className="welcome-card-title">Scrape News</div>
                        <div className="welcome-card-desc">
                            Extract headlines and links from news sites
                        </div>
                    </div>
                    <div
                        className="welcome-card"
                        onClick={() =>
                            onExampleClick(
                                "Scrape https://quotes.toscrape.com and get me all quotes with the author name and tags. Output as JSON."
                            )
                        }
                    >
                        <div className="welcome-card-icon">💬</div>
                        <div className="welcome-card-title">Collect Quotes</div>
                        <div className="welcome-card-desc">
                            Gather quotes, authors, and tags from pages
                        </div>
                    </div>
                    <div
                        className="welcome-card"
                        onClick={() =>
                            onExampleClick(
                                "Scrape https://books.toscrape.com and get me the book title, price, and rating. Output as XLSX."
                            )
                        }
                    >
                        <div className="welcome-card-icon">📚</div>
                        <div className="welcome-card-title">Product Data</div>
                        <div className="welcome-card-desc">
                            Extract product listings with prices and details
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    return (
        <div className="chat-messages" id="chat-messages">
            {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
            ))}
            {/* Pipeline progress */}
            {pipelineState && Object.keys(pipelineState).length > 0 && (
                <PipelineProgress state={pipelineState} />
            )}
            {/* Data preview */}
            {previewData && (
                <DataPreview
                    preview={previewData.preview}
                    validation={previewData.validation}
                    onApprove={onApprove}
                    onRetry={onRetry}
                />
            )}
            {/* Typing indicator */}
            {isLoading && !pipelineState && (
                <div className="message assistant">
                    <div className="message-avatar">🤖</div>
                    <div className="typing-indicator">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                    </div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    );
}
