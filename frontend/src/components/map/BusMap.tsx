import { MapContainer, TileLayer } from 'react-leaflet';

import type { BusWithLocation } from '../../hooks/useBusLocations';
import type { Route } from '../../types/domain';
import { BusMarker } from './BusMarker';
import { RoutePolyline } from './RoutePolyline';

type BusMapProps = {
  busesWithLocations: BusWithLocation[];
  routeMap: Record<number, Pick<Route, 'name' | 'stop_count'>>;
  routeId: number | null;
  isLoading: boolean;
  error: string | null;
  busesWithoutLocation: number;
  invalidLocationCount: number;
};

const UTTAR_PRADESH_CENTER: [number, number] = [26.8467, 80.9462];
const INITIAL_ZOOM = 7;

export function BusMap({
  busesWithLocations,
  routeMap,
  routeId,
  isLoading,
  error,
  busesWithoutLocation,
  invalidLocationCount,
}: BusMapProps) {
  const visibleBusCount = busesWithLocations.filter(
    (item) => item.location !== null && item.coordinateError === null,
  ).length;

  return (
    <section className="panel map-panel" aria-label="Live bus map">
      <div className="panel-header">
        <div>
          <h2>Live Bus Map</h2>
          <p>OpenStreetMap view centered on Uttar Pradesh</p>
        </div>
        <span className="map-count">{visibleBusCount} visible</span>
      </div>

      <div className="map-shell">
        {isLoading ? <div className="map-overlay">Loading map</div> : null}
        {error ? <div className="map-overlay map-overlay-error">{error}</div> : null}
        {!isLoading && !error && busesWithoutLocation > 0 ? (
          <div className="map-message">
            No location available for {busesWithoutLocation} bus
            {busesWithoutLocation === 1 ? '' : 'es'}
          </div>
        ) : null}
        {!isLoading && !error && invalidLocationCount > 0 ? (
          <div className="map-message map-message-warning">
            {invalidLocationCount} invalid coordinate record ignored
          </div>
        ) : null}

        <MapContainer
          center={UTTAR_PRADESH_CENTER}
          zoom={INITIAL_ZOOM}
          scrollWheelZoom
          className="bus-map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <RoutePolyline routeId={routeId} />
          {busesWithLocations.map((item) => (
            <BusMarker key={item.bus.id} item={item} routeMap={routeMap} />
          ))}
        </MapContainer>
      </div>
    </section>
  );
}
