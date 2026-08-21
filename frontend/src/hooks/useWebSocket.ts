import { useEffect, useRef, useState, useCallback } from 'react';
import type { PriceUpdate } from '../types/api';

interface UseWebSocketReturn {
  prices: Map<string, PriceUpdate>;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  connected: boolean;
}

const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function useWebSocket(): UseWebSocketReturn {
  const [prices, setPrices] = useState<Map<string, PriceUpdate>>(new Map());
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const subscribedSymbols = useRef<Set<string>>(new Set());
  const unmountedRef = useRef(false);

  const getWsUrl = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${location.host}/ws/prices?token=${token}`;
  }, []);

  const sendMessage = useCallback((msg: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const url = getWsUrl();
    if (!url) return;

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (unmountedRef.current) return;
      setConnected(true);
      reconnectAttempts.current = 0;
      // Resubscribe to previously subscribed symbols
      if (subscribedSymbols.current.size > 0) {
        ws.send(JSON.stringify({
          action: 'subscribe',
          symbols: Array.from(subscribedSymbols.current),
        }));
      }
    };

    ws.onmessage = (event) => {
      if (unmountedRef.current) return;
      try {
        const msg = JSON.parse(event.data as string);
        if (msg.type === 'ping') {
          sendMessage({ type: 'pong' });
        } else if (msg.type === 'price_update' && msg.data) {
          const update = msg.data as PriceUpdate;
          setPrices((prev) => {
            const next = new Map(prev);
            next.set(update.symbol, update);
            return next;
          });
        } else if (msg.type === 'error' && msg.code === 40101) {
          // Token expired, don't reconnect
          ws.close();
        }
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      setConnected(false);
      wsRef.current = null;
      // Auto-reconnect with backoff
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY_MS * Math.pow(1.5, reconnectAttempts.current);
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror
    };
  }, [getWsUrl, sendMessage]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const subscribe = useCallback((symbols: string[]) => {
    symbols.forEach((s) => subscribedSymbols.current.add(s));
    sendMessage({ action: 'subscribe', symbols });
  }, [sendMessage]);

  const unsubscribe = useCallback((symbols: string[]) => {
    symbols.forEach((s) => subscribedSymbols.current.delete(s));
    sendMessage({ action: 'unsubscribe', symbols });
  }, [sendMessage]);

  return { prices, subscribe, unsubscribe, connected };
}
