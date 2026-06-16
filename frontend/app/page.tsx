"use client";
import { useState, useCallback, useEffect } from "react";
import Sidebar from "@/components/Sidebar/Sidebar";
import ChatArea from "@/components/Chat/ChatArea";
import MessageInput from "@/components/Chat/MessageInput";
import {
  Session,
  Message,
  DataPreview,
  ValidationResult,
} from "@/lib/types";
import {
  createSession,
  listSessions,
  deleteSession,
  getChatHistory,
  sendMessage,
  getDownloadUrl,
} from "@/lib/api";
interface PipelineState {
  [key: string]: {
    status: "pending" | "running" | "completed" | "error";
    detail: string;
    progress?: number;
  };
}
export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [pipelineState, setPipelineState] = useState<PipelineState | null>(null);
  const [previewData, setPreviewData] = useState<{
    preview: DataPreview;
    validation?: ValidationResult;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);
  const loadSessions = async () => {
    try {
      const data = await listSessions();
      setSessions(data);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };
  const loadMessages = async (sessionId: string) => {
    try {
      const data = await getChatHistory(sessionId);
      setMessages(data);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };
  const handleNewChat = useCallback(async () => {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setPipelineState(null);
      setPreviewData(null);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }, []);
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      setPipelineState(null);
      setPreviewData(null);
      await loadMessages(sessionId);
    },
    []
  );
  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      try {
        await deleteSession(sessionId);
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setMessages([]);
          setPipelineState(null);
          setPreviewData(null);
        }
      } catch (err) {
        console.error("Failed to delete session:", err);
      }
    },
    [activeSessionId]
  );
  const handleSendMessage = useCallback(
    async (content: string, fileIds: string[]) => {
      if (!activeSessionId || !content.trim()) return;
      // Add user message optimistically
      const userMsg: Message = {
        id: `temp-${Date.now()}`,
        session_id: activeSessionId,
        role: "user",
        content,
        message_type: "text",
        metadata: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setPipelineState(null);
      setPreviewData(null);
      try {
        for await (const event of sendMessage(activeSessionId, content, fileIds)) {
          switch (event.event) {
            case "message":
              const assistantMsg: Message = {
                id: `msg-${Date.now()}-${Math.random()}`,
                session_id: activeSessionId,
                role: event.data.role || "assistant",
                content: event.data.content || "",
                message_type: "text",
                metadata: {},
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              break;
            case "pipeline_update":
              setPipelineState((prev) => ({
                ...prev,
                [event.data.step]: {
                  status: event.data.status,
                  detail: event.data.detail,
                  progress: event.data.progress,
                },
              }));
              break;
            case "preview":
              setPreviewData({
                preview: event.data.preview,
                validation: event.data.validation,
              });
              if (event.data.message) {
                const previewMsg: Message = {
                  id: `msg-${Date.now()}-preview`,
                  session_id: activeSessionId,
                  role: "assistant",
                  content: event.data.message,
                  message_type: "preview",
                  metadata: {},
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, previewMsg]);
              }
              break;
            case "export":
              if (event.data.download_url) {
                window.open(getDownloadUrl(event.data.filename), "_blank");
              }
              if (event.data.message) {
                const exportMsg: Message = {
                  id: `msg-${Date.now()}-export`,
                  session_id: activeSessionId,
                  role: "assistant",
                  content: event.data.message,
                  message_type: "export",
                  metadata: {},
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, exportMsg]);
              }
              setPreviewData(null);
              setPipelineState(null);
              break;
            case "error":
              const errorMsg: Message = {
                id: `msg-${Date.now()}-error`,
                session_id: activeSessionId,
                role: "assistant",
                content: event.data.message || "An error occurred.",
                message_type: "error",
                metadata: {},
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, errorMsg]);
              break;
            case "done":
              break;
          }
        }
      } catch (err) {
        console.error("Message send failed:", err);
        const errorMsg: Message = {
          id: `msg-${Date.now()}-error`,
          session_id: activeSessionId,
          role: "assistant",
          content: `❌ Connection error: ${err instanceof Error ? err.message : "Unknown error"}. Is the backend running?`,
          message_type: "error",
          metadata: {},
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
        // Refresh sessions to update title
        loadSessions();
      }
    },
    [activeSessionId]
  );
  const handleApprove = useCallback(
    (format: string) => {
      if (!activeSessionId) return;
      handleSendMessage(`Approve the data and export as ${format}`, []);
    },
    [activeSessionId, handleSendMessage]
  );
  const handleRetry = useCallback(() => {
    if (!activeSessionId) return;
    handleSendMessage("Retry the scraping with a different approach", []);
  }, [activeSessionId, handleSendMessage]);
  const handleExampleClick = useCallback(
    (text: string) => {
      if (!activeSessionId) {
        // Create a new session first, then send
        createSession().then((session) => {
          setSessions((prev) => [session, ...prev]);
          setActiveSessionId(session.id);
          setMessages([]);
          // Small delay so state settles
          setTimeout(() => {
            handleSendMessageForSession(session.id, text);
          }, 100);
        });
      } else {
        handleSendMessage(text, []);
      }
    },
    [activeSessionId, handleSendMessage]
  );
  // Helper for sending to a specific session (used by example click)
  const handleSendMessageForSession = async (
    sessionId: string,
    content: string
  ) => {
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content,
      message_type: "text",
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages([userMsg]);
    setIsLoading(true);
    try {
      for await (const event of sendMessage(sessionId, content, [])) {
        switch (event.event) {
          case "message":
            const msg: Message = {
              id: `msg-${Date.now()}-${Math.random()}`,
              session_id: sessionId,
              role: event.data.role || "assistant",
              content: event.data.content || "",
              message_type: "text",
              metadata: {},
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, msg]);
            break;
          case "pipeline_update":
            setPipelineState((prev) => ({
              ...prev,
              [event.data.step]: {
                status: event.data.status,
                detail: event.data.detail,
                progress: event.data.progress,
              },
            }));
            break;
          case "preview":
            setPreviewData({
              preview: event.data.preview,
              validation: event.data.validation,
            });
            if (event.data.message) {
              setMessages((prev) => [
                ...prev,
                {
                  id: `msg-${Date.now()}-preview`,
                  session_id: sessionId,
                  role: "assistant",
                  content: event.data.message,
                  message_type: "preview",
                  metadata: {},
                  created_at: new Date().toISOString(),
                },
              ]);
            }
            break;
          case "error":
            setMessages((prev) => [
              ...prev,
              {
                id: `msg-${Date.now()}-error`,
                session_id: sessionId,
                role: "assistant",
                content: event.data.message || "An error occurred.",
                message_type: "error",
                metadata: {},
                created_at: new Date().toISOString(),
              },
            ]);
            break;
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}-error`,
          session_id: sessionId,
          role: "assistant",
          content: `❌ Connection error. Is the backend running on http://localhost:8000?`,
          message_type: "error",
          metadata: {},
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
      loadSessions();
    }
  };
  const activeSession = sessions.find((s) => s.id === activeSessionId);

    return (
            <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />
      <main className="main-area">
        <header className="chat-header">
          <h2 className="chat-header-title">
            {activeSession?.title || "AI Scraper Engine"}
          </h2>
        </header>
        <ChatArea
          messages={messages}
          pipelineState={pipelineState}
          previewData={previewData}
          isLoading={isLoading}
          onApprove={handleApprove}
          onRetry={handleRetry}
          onExampleClick={handleExampleClick}
        />
        <MessageInput
          sessionId={activeSessionId}
          onSend={handleSendMessage}
          disabled={isLoading}
        />
      </main>
    </div>
  );
}
