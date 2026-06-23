import { env } from '../../config/env';
import type { BusLocation, LocationSocketMessage } from '../../types/domain';

type BusLocationSocketHandlers = {
  onOpen?: () => void;
  onClose?: () => void;
  onLocation?: (location: BusLocation) => void;
  onError?: (event: Event) => void;
};

export type BusLocationSocket = {
  close: () => void;
};

const INITIAL_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 15_000;

export function createBusLocationSocket(
  busId: number,
  handlers: BusLocationSocketHandlers,
): BusLocationSocket {
  const url = new URL(`/ws/buses/${busId}`, env.wsBaseUrl);
  let socket: WebSocket | null = null;
  let reconnectDelayMs = INITIAL_RECONNECT_DELAY_MS;
  let reconnectTimer: number | null = null;
  let closedByClient = false;

  function scheduleReconnect() {
    if (closedByClient || reconnectTimer !== null) {
      return;
    }

    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, reconnectDelayMs);
    reconnectDelayMs = Math.min(reconnectDelayMs * 2, MAX_RECONNECT_DELAY_MS);
  }

  function connect() {
    socket = new WebSocket(url);

    socket.addEventListener('open', () => {
      reconnectDelayMs = INITIAL_RECONNECT_DELAY_MS;
      handlers.onOpen?.();
    });

    socket.addEventListener('close', () => {
      handlers.onClose?.();
      scheduleReconnect();
    });

    socket.addEventListener('error', (event) => {
      handlers.onError?.(event);
    });

    socket.addEventListener('message', (event) => {
      try {
        const message = JSON.parse(event.data as string) as LocationSocketMessage;
        if (message.type === 'location_update' || message.type === 'latest_location') {
          handlers.onLocation?.(message.data);
        }
      } catch {
        handlers.onError?.(event);
      }
    });
  }

  connect();

  return {
    close: () => {
      closedByClient = true;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    },
  };
}
