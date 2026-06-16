"use client";

import ChatInput from "./ChatInput";
import { useChat } from "@/hooks/useChat";

export default function ChatArea() {
  const { messages, isConnected, sendMessage } = useChat();

  return (
    <div className="flex flex-col h-full w-full relative">
      {/* Header */}
      <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-black/20">
        <h3 className="font-medium text-gray-200">Current Task: <span className="text-blue-400">Untitled</span></h3>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-xs text-gray-500">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex gap-4 max-w-3xl">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold">AI</span>
            </div>
            <div className="bg-[var(--message-ai-bg)] p-4 rounded-2xl rounded-tl-none border border-white/5">
              <p className="text-gray-200 leading-relaxed">
                Hello! I'm your AI Scraping Assistant. What would you like to scrape today? You can provide a URL, upload a file with URLs, and tell me what data you need.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => {
          const isUser = msg.data?.sender === 'user';
          if (msg.type === 'progress') {
            return (
              <div key={idx} className="flex gap-4 max-w-3xl">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-gray-400">⚙️</span>
                </div>
                <div className="bg-white/5 p-3 rounded-2xl rounded-tl-none border border-white/10 text-sm text-gray-300">
                  <p className="font-medium text-blue-400 mb-1 capitalize">[{msg.data?.stage || 'Progress'}]</p>
                  <p>{msg.content}</p>
                </div>
              </div>
            );
          }

          if (msg.type === 'preview') {
            return (
              <div key={idx} className="flex gap-4 max-w-3xl">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold">AI</span>
                </div>
                <div className="bg-[var(--message-ai-bg)] p-4 rounded-2xl rounded-tl-none border border-green-500/30 w-full overflow-x-auto">
                  <p className="text-gray-200 mb-3 font-medium">Data Preview:</p>
                  <pre className="text-xs text-green-300 bg-black/50 p-3 rounded">{JSON.stringify(msg.data?.preview_data, null, 2)}</pre>
                </div>
              </div>
            );
          }

          return (
            <div key={idx} className={`flex gap-4 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-gray-700' : 'bg-gradient-to-br from-blue-500 to-purple-600'}`}>
                <span className="text-xs font-bold">{isUser ? 'U' : 'AI'}</span>
              </div>
              <div className={`p-4 rounded-2xl border ${isUser ? 'bg-[var(--message-user-bg)] rounded-tr-none border-blue-500/20 text-blue-50' : 'bg-[var(--message-ai-bg)] rounded-tl-none border-white/5 text-gray-200'}`}>
                <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-black/20 backdrop-blur-md border-t border-white/5">
        <ChatInput onSend={(text) => sendMessage(text, 'text')} disabled={!isConnected} />
      </div>
    </div>
  );
}
