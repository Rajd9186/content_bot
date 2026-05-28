export type WebSocketMessage = Record<string, unknown>;

export type MessageHandler = (data: WebSocketMessage) => void;

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

interface SocketConfig {
  url: string;
  reconnectBaseDelayMs?: number;
  reconnectMaxDelayMs?: number;
  maxReconnectAttempts?: number;
  heartbeatIntervalMs?: number;
}

const DEFAULT_CONFIG: Required<Omit<SocketConfig, "url">> = {
  reconnectBaseDelayMs: 1000,
  reconnectMaxDelayMs: 30000,
  maxReconnectAttempts: 10,
  heartbeatIntervalMs: 30000,
};

export class SocketClient {
  private socket: WebSocket | null = null;
  private handlers = new Map<string, Set<MessageHandler>>();
  private config: Required<SocketConfig>;
  private reconnectAttempt = 0;
  private intentionalClose = false;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();

  constructor(config: SocketConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    this.intentionalClose = false;
    this.setStatus("connecting");

    this.socket = new WebSocket(this.config.url);

    this.socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.setStatus("connected");
      this.startHeartbeat();
    };

    this.socket.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        const type = (message.type as string) || "message";
        const typeHandlers = this.handlers.get(type);
        const allHandlers = this.handlers.get("*");

        typeHandlers?.forEach((handler) => handler(message));
        allHandlers?.forEach((handler) => handler(message));
      } catch {
        console.error("[WS] Failed to parse message:", event.data);
      }
    };

    this.socket.onclose = () => {
      this.stopHeartbeat();
      if (!this.intentionalClose && this.reconnectAttempt < this.config.maxReconnectAttempts) {
        this.scheduleReconnect();
      } else {
        this.setStatus("disconnected");
      }
    };

    this.socket.onerror = () => {
      this.socket?.close();
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.stopHeartbeat();
    this.socket?.close();
    this.socket = null;
    this.setStatus("disconnected");
  }

  send(type: string, payload: Record<string, unknown> = {}): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, ...payload, timestamp: new Date().toISOString() }));
    }
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }

  getStatus(): ConnectionStatus {
    if (!this.socket || this.socket.readyState === WebSocket.CLOSED) return "disconnected";
    if (this.socket.readyState === WebSocket.CONNECTING) return "connecting";
    if (this.socket.readyState === WebSocket.OPEN) return "connected";
    return "disconnected";
  }

  private scheduleReconnect(): void {
    this.reconnectAttempt++;
    const delay = Math.min(
      this.config.reconnectBaseDelayMs * Math.pow(2, this.reconnectAttempt - 1),
      this.config.reconnectMaxDelayMs,
    );
    const jitter = delay * (0.5 + Math.random() * 0.5);

    this.setStatus("reconnecting");
    setTimeout(() => this.connect(), jitter);
  }

  private setStatus(status: ConnectionStatus): void {
    this.statusListeners.forEach((listener) => listener(status));
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.send("ping");
    }, this.config.heartbeatIntervalMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}
