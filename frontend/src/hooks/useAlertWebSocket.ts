import { useEffect, useRef, useCallback } from 'react';
import { notification } from 'antd';
import type { AlertTriggeredEvent } from '../types/api';

const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function useAlertWebSocket(): void {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  const getWsUrl = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${location.host}/ws/alerts?token=${token}`;
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
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      if (unmountedRef.current) return;
      try {
        const msg = JSON.parse(event.data as string);
        if (msg.type === 'ping') {
          sendMessage({ type: 'pong' });
        } else if (msg.type === 'alert_triggered' && msg.data) {
          const data = msg.data as AlertTriggeredEvent;
          notification.warning({
            message: `🔔 告警触发 - ${data.coin_symbol}`,
            description: data.message,
            duration: 8,
            placement: 'topRight',
          });
        } else if (msg.type === 'error' && msg.code === 40101) {
          ws.close();
        }
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      wsRef.current = null;
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
}
