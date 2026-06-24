import { useEffect, useMemo, useState } from 'react';

import { BusList } from '../components/bus/BusList';
import { AppShell } from '../components/layout/AppShell';
import { BusMap } from '../components/map/BusMap';
import { RouteStopsPanel } from '../components/routes/RouteStopsPanel';
import { StatusCard } from '../components/status/StatusCard';
import { useBusLocations } from '../hooks/useBusLocations';
import { fetchRoutes } from '../services/api/routeApi';
import type { Route } from '../types/domain';

export function App() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
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

  useEffect(() => {
    if (selectedRouteId !== null) {
      return;
    }

    if (routes.length > 0) {
      setSelectedRouteId(routes[0].id);
    }
  }, [routes, selectedRouteId]);

  const routeMap = useMemo(
    () =>
      routes.reduce<Record<number, Pick<Route, 'name' | 'stop_count'>>>((acc, route) => {
        acc[route.id] = { name: route.name, stop_count: route.stop_count };
        return acc;
      }, {}),
    [routes],
  );

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

      <section className="panel" aria-label="Route selection">
        <div className="panel-header">
          <div>
            <h2>Route visualization</h2>
            <p>Select a route to show stops and geometry.</p>
          </div>
        </div>
        <div className="route-selector">
          <label htmlFor="route-select">Route</label>
          <select
            id="route-select"
            value={selectedRouteId ?? ''}
            onChange={(event) => setSelectedRouteId(Number(event.target.value))}
          >
            {routes.map((route) => (
              <option key={route.id} value={route.id}>
                {route.route_number} — {route.name}
              </option>
            ))}
          </select>
        </div>
      </section>

      <BusMap
        busesWithLocations={busesWithLocations}
        routeMap={routeMap}
        routeId={selectedRouteId}
        isLoading={busLocationStatus === 'loading'}
        error={busLocationError}
        busesWithoutLocation={busesWithoutLocation}
        invalidLocationCount={invalidLocationCount}
      />

      {selectedRouteId !== null ? (
        <RouteStopsPanel routeId={selectedRouteId} routeMap={routeMap} />
      ) : null}

      <BusList buses={buses} isLoading={busLocationStatus === 'loading'} />
    </AppShell>
  );
}
