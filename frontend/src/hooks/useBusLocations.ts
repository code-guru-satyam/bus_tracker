import { useCallback, useEffect, useMemo, useState } from 'react';

import { fetchBuses } from '../services/api/busApi';
import { fetchLatestBusLocation } from '../services/api/locationApi';
import type { Bus, BusLocation } from '../types/domain';
import { useBusLocationSockets } from './useBusLocationSockets';

export type BusLocationStatus = 'loading' | 'ready' | 'error';

export type BusWithLocation = {
  bus: Bus;
  location: BusLocation | null;
  coordinateError: string | null;
};

type UseBusLocationsResult = {
  buses: Bus[];
  busesWithLocations: BusWithLocation[];
  status: BusLocationStatus;
  error: string | null;
  busesWithoutLocation: number;
  invalidLocationCount: number;
};

function isValidCoordinate(latitude: string, longitude: string): boolean {
  const parsedLatitude = Number(latitude);
  const parsedLongitude = Number(longitude);

  return (
    Number.isFinite(parsedLatitude) &&
    Number.isFinite(parsedLongitude) &&
    parsedLatitude >= -90 &&
    parsedLatitude <= 90 &&
    parsedLongitude >= -180 &&
    parsedLongitude <= 180
  );
}

function getCoordinateError(location: BusLocation | null): string | null {
  if (location === null) {
    return null;
  }

  if (!isValidCoordinate(location.latitude, location.longitude)) {
    return 'Invalid coordinates';
  }

  return null;
}

export function useBusLocations(): UseBusLocationsResult {
  const [buses, setBuses] = useState<Bus[]>([]);
  const [locationsByBusId, setLocationsByBusId] = useState<Record<number, BusLocation>>({});
  const [status, setStatus] = useState<BusLocationStatus>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadBusesAndLocations() {
      setStatus('loading');
      setError(null);

      try {
        const busData = await fetchBuses();
        const locationResults = await Promise.allSettled(
          busData.map(async (bus) => ({
            busId: bus.id,
            location: await fetchLatestBusLocation(bus.id),
          })),
        );

        if (!isMounted) {
          return;
        }

        const nextLocations: Record<number, BusLocation> = {};
        let hasLocationRequestError = false;
        for (const result of locationResults) {
          if (result.status === 'fulfilled' && result.value.location !== null) {
            nextLocations[result.value.busId] = result.value.location;
          }
          if (result.status === 'rejected') {
            hasLocationRequestError = true;
          }
        }

        setBuses(busData);
        setLocationsByBusId(nextLocations);
        if (hasLocationRequestError) {
          setStatus('error');
          setError('API unavailable');
          return;
        }
        setStatus('ready');
      } catch {
        if (isMounted) {
          setStatus('error');
          setError('API unavailable');
        }
      }
    }

    loadBusesAndLocations();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRealtimeLocation = useCallback((busId: number, location: BusLocation) => {
    setLocationsByBusId((currentLocations) => ({
      ...currentLocations,
      [busId]: location,
    }));
  }, []);

  useBusLocationSockets({
    buses,
    onLocation: handleRealtimeLocation,
  });

  const busesWithLocations = useMemo(
    () =>
      buses.map((bus) => {
        const location = locationsByBusId[bus.id] ?? null;
        return {
          bus,
          location,
          coordinateError: getCoordinateError(location),
        };
      }),
    [buses, locationsByBusId],
  );

  const busesWithoutLocation = useMemo(
    () => busesWithLocations.filter((item) => item.location === null).length,
    [busesWithLocations],
  );

  const invalidLocationCount = useMemo(
    () => busesWithLocations.filter((item) => item.coordinateError !== null).length,
    [busesWithLocations],
  );

  return {
    buses,
    busesWithLocations,
    status,
    error,
    busesWithoutLocation,
    invalidLocationCount,
  };
}
