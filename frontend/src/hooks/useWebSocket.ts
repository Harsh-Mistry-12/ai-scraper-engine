import { useState, useEffect, useRef, useCallback } from 'react';

export type WebSocketMessage = {
  type: 'text' | 'progress' | 'analysis' | 'strategy' | 'preview' | 'error';
  content: string;
  data?: any;
};

export function useWebSocket(sessionId: str) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;
    
    // Default to localhost:8000 for backend
    const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, message]);
      } catch (e) {
        // Fallback for simple text messages
        setMessages((prev) => [...prev, { type: 'text', content: event.data }]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [sessionId]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendMessage = useCallback((content: string, type: string = 'text') => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({ type, content }));
      // Optimistically add user message to UI
      if (type === 'text') {
        setMessages((prev) => [...prev, { type: 'text', content, data: { sender: 'user' } }]);
      }
    } else {
      console.error('WebSocket is not connected');
    }
  }, [isConnected]);

  return { messages, isConnected, sendMessage, setMessages };
}
