/**
 * WebSocket client for communicating with the Dreamscape backend.
 */

import type { WSMessage, MessageType } from '../types/world';

type MessageHandler = (data: Record<string, unknown>) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<MessageType, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly sessionId: string;
  private url: string;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/ws/${sessionId}`;
  }

  connect(): void {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as WSMessage;
        const handlers = this.handlers.get(msg.type);
        if (handlers) {
          for (const handler of handlers) {
            handler(msg.data);
          }
        }
      } catch (e) {
        console.error('[WS] Failed to parse message:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('[WS] Disconnected');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        console.log(`[WS] Reconnecting in ${delay}ms...`);
        setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = (e) => {
      console.error('[WS] Error:', e);
    };
  }

  on(type: MessageType, handler: MessageHandler): void {
    const existing = this.handlers.get(type) ?? [];
    existing.push(handler);
    this.handlers.set(type, existing);
  }

  send(type: MessageType, data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('[WS] Not connected, cannot send');
    }
  }

  sendUserInput(text: string): void {
    this.send('user_input', { text });
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
