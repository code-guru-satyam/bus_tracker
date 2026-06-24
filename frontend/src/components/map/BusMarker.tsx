import L from 'leaflet';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Marker, Popup } from 'react-leaflet';

import type { BusWithLocation } from '../../hooks/useBusLocations';

type BusMarkerProps = {
  item: BusWithLocation;
  routeMap: Record<number, { name: string; stop_count: number }>;
};

const busMarkerIcon = L.divIcon({
  className: 'bus-marker-icon',
  html: '<span></span>',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
  popupAnchor: [0, -14],
});

const MARKER_ANIMATION_MS = 900;

function easeOutCubic(progress: number): number {
  return 1 - Math.pow(1 - progress, 3);
}

export function BusMarker({ item, routeMap }: BusMarkerProps) {
  const animationFrameRef = useRef<number | null>(null);
  const targetPosition = useMemo<[number, number] | null>(() => {
    if (item.location === null || item.coordinateError !== null) {
      return null;
    }

    return [Number(item.location.latitude), Number(item.location.longitude)];
  }, [item.coordinateError, item.location]);
  const [displayPosition, setDisplayPosition] = useState<[number, number] | null>(targetPosition);
  const displayPositionRef = useRef<[number, number] | null>(targetPosition);

  function updateDisplayPosition(position: [number, number] | null) {
    displayPositionRef.current = position;
    setDisplayPosition(position);
  }

  useEffect(() => {
    if (targetPosition === null) {
      return;
    }

    if (displayPositionRef.current === null) {
      animationFrameRef.current = window.requestAnimationFrame(() => {
        updateDisplayPosition(targetPosition);
      });
      return;
    }

    const startPosition = displayPositionRef.current;
    const endPosition = targetPosition;
    const startedAt = performance.now();

    function animateFrame(now: number) {
      const progress = Math.min((now - startedAt) / MARKER_ANIMATION_MS, 1);
      const easedProgress = easeOutCubic(progress);
      const nextLatitude =
        startPosition[0] + (endPosition[0] - startPosition[0]) * easedProgress;
      const nextLongitude =
        startPosition[1] + (endPosition[1] - startPosition[1]) * easedProgress;

      updateDisplayPosition([nextLatitude, nextLongitude]);

      if (progress < 1) {
        animationFrameRef.current = window.requestAnimationFrame(animateFrame);
      }
    }

    if (animationFrameRef.current !== null) {
      window.cancelAnimationFrame(animationFrameRef.current);
    }
    animationFrameRef.current = window.requestAnimationFrame(animateFrame);

    return () => {
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [targetPosition]);

  if (item.location === null || item.coordinateError !== null) {
    return null;
  }

  if (displayPosition === null) {
    return null;
  }

  return (
    <Marker position={displayPosition} icon={busMarkerIcon}>
      <Popup>
        <div className="bus-popup">
          <strong>Bus {item.bus.id}</strong>
          <dl>
            <div>
              <dt>Registration Number</dt>
              <dd>{item.bus.registration_number}</dd>
            </div>
            <div>
              <dt>Route Name</dt>
              <dd>
                {item.bus.route_id != null && routeMap[item.bus.route_id]
                  ? routeMap[item.bus.route_id].name
                  : '-'}
              </dd>
            </div>
            <div>
              <dt>Total Stops</dt>
              <dd>
                {item.bus.route_id != null && routeMap[item.bus.route_id]
                  ? routeMap[item.bus.route_id].stop_count
                  : '-'}
              </dd>
            </div>
            <div>
              <dt>Next Stop</dt>
              <dd>Coming soon</dd>
            </div>
            <div>
              <dt>Speed</dt>
              <dd>{item.location.speed_kmph ?? '-'} km/h</dd>
            </div>
            <div>
              <dt>Last update</dt>
              <dd>{new Date(item.location.recorded_at).toLocaleString()}</dd>
            </div>
          </dl>
        </div>
      </Popup>
    </Marker>
  );
}
