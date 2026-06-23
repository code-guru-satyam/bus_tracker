import { useEffect, useMemo, useState } from 'react';

import { BusList } from '../components/bus/BusList';
import { AppShell } from '../components/layout/AppShell';
import { BusMap } from '../components/map/BusMap';
import { StatusCard } from '../components/status/StatusCard';
import { useBusLocations } from '../hooks/useBusLocations';
import { fetchRoutes } from '../services/api/routeApi';
import type { Route } from '../types/domain';

export function App() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [routeStatus, setRouteStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const {
    buses,
    busesWithLocations,
    status: busLocationStatus,
    error: busLocationError,
    busesWithoutLocation,
    invalidLocationCount,
  } = useBusLocations();

  useEffect(() => {
    let isMounted = true;

    async function loadRoutes() {
      setRouteStatus('loading');
      try {
        const routeData = await fetchRoutes();
        if (!isMounted) {
          return;
        }
        setRoutes(routeData);
        setRouteStatus('ready');
      } catch {
        if (isMounted) {
          setRouteStatus('error');
        }
      }
    }

    loadRoutes();

    return () => {
      isMounted = false;
    };
  }, []);

  const activeBuses = useMemo(() => buses.filter((bus) => bus.is_active).length, [buses]);
  const visibleBuses = useMemo(
    () =>
      busesWithLocations.filter((item) => item.location !== null && item.coordinateError === null)
        .length,
    [busesWithLocations],
  );
  const apiStatus = busLocationStatus === 'error' || routeStatus === 'error' ? 'error' : 'ready';

  return (
    <AppShell>
      <section className="dashboard-grid" aria-label="Bus tracking overview">
        <StatusCard label="API" value={apiStatus} tone={apiStatus === 'error' ? 'danger' : 'ok'} />
        <StatusCard label="Map markers" value={visibleBuses.toString()} tone="neutral" />
        <StatusCard label="Routes" value={routes.length.toString()} tone="neutral" />
        <StatusCard label="Active buses" value={activeBuses.toString()} tone="neutral" />
      </section>

      <BusMap
        busesWithLocations={busesWithLocations}
        isLoading={busLocationStatus === 'loading'}
        error={busLocationError}
        busesWithoutLocation={busesWithoutLocation}
        invalidLocationCount={invalidLocationCount}
      />

      <BusList buses={buses} isLoading={busLocationStatus === 'loading'} />
    </AppShell>
  );
}
