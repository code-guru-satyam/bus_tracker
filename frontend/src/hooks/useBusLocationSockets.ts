import { useEffect } from 'react';

import { createBusLocationSocket } from '../services/websocket/busLocationSocket';
import type { Bus, BusLocation } from '../types/domain';

type UseBusLocationSocketsParams = {
  buses: Bus[];
  onLocation: (busId: number, location: BusLocation) => void;
};

export function useBusLocationSockets({ buses, onLocation }: UseBusLocationSocketsParams): void {
  useEffect(() => {
    if (buses.length === 0) {
      return;
    }

    const sockets = buses.map((bus) =>
      createBusLocationSocket(bus.id, {
        onLocation: (location) => onLocation(bus.id, location),
      }),
    );

    return () => {
      for (const socket of sockets) {
        socket.close();
      }
    };
  }, [buses, onLocation]);
}
