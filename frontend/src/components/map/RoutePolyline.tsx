import { useEffect, useState } from 'react';
import { Polyline, useMap } from 'react-leaflet';

import type { RouteGeometry } from '../../types/domain';
import { fetchRouteGeometry } from '../../services/api/routeApi';

type RoutePolylineProps = {
  routeId: number | null;
};

const polylineOptions = {
  color: '#147d64',
  weight: 4,
  opacity: 0.78,
};

export function RoutePolyline({ routeId }: RoutePolylineProps) {
  const map = useMap();
  const [coordinates, setCoordinates] = useState<Array<[number, number]>>([]);

  useEffect(() => {
    let active = true;
    if (routeId === null) {
      setCoordinates([]);
      return () => {
        active = false;
      };
    }

    fetchRouteGeometry(routeId)
      .then((routeGeometry: RouteGeometry) => {
        if (!active) {
          return;
        }
        setCoordinates(routeGeometry.coordinates);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setCoordinates([]);
      });

    return () => {
      active = false;
    };
  }, [routeId]);

  useEffect(() => {
    if (coordinates.length === 0) {
      return;
    }

    try {
      map.fitBounds(coordinates, {
        padding: [40, 40],
      });
    } catch {
      // Ignore failures during map updates.
    }
  }, [coordinates, map]);

  if (coordinates.length === 0) {
    return null;
  }

  return <Polyline pathOptions={polylineOptions} positions={coordinates} />;
}
