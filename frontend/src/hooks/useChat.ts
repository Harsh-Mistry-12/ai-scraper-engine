import { useState } from 'react';
import { useWebSocket } from './useWebSocket';

export function useChat() {
  // Hardcoded session ID for dev, in prod this would be dynamic
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const { messages, isConnected, sendMessage } = useWebSocket(sessionId);

  return {
    sessionId,
    messages,
    isConnected,
    sendMessage
  };
}
