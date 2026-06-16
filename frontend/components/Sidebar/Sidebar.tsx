"use client";
import { Session } from "@/lib/types";
interface SidebarProps {
    sessions: Session[];
    activeSessionId: string | null;
    onSelectSession: (id: string) => void;
    onNewChat: () => void;
    onDeleteSession: (id: string) => void;
}
export default function Sidebar({
    sessions,
    activeSessionId,
    onSelectSession,
    onNewChat,
    onDeleteSession,
}: SidebarProps) {
    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };
    return (
        <aside className="sidebar" id="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="sidebar-logo-icon">⚡</div>
                    <span className="sidebar-logo-text">AI Scraper</span>
                </div>
                <button className="new-chat-btn" onClick={onNewChat} id="new-chat-btn">
                    <span className="icon">+</span>
                    New Chat
                </button>
            </div>
            <div className="sidebar-sessions" id="session-list">
                {sessions.length === 0 ? (
                    <div className="empty-sessions">
                        No conversations yet.
                        <br />
                        Start a new chat to begin scraping!
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`session-item ${session.id === activeSessionId ? "active" : ""
                                }`}
                            onClick={() => onSelectSession(session.id)}
                            id={`session-${session.id}`}
                        >
                            <div className="session-item-content">
                                <div className="session-item-title">{session.title}</div>
                                <div className="session-item-date">
                                    {formatDate(session.updated_at)}
                                </div>
                            </div>
                            <button
                                className="session-delete-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteSession(session.id);
                                }}
                                title="Delete chat"
                            >
                                🗑️
                            </button>
                        </div>
                    ))
                )}
            </div>
        </aside>
    );
}
