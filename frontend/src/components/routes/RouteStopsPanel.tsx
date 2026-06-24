import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';

import type {
  Route,
  RouteStop,
  RouteStopCreate,
  RouteStopUpdate,
} from '../../types/domain';
import {
  createRouteStop,
  deleteRouteStop,
  fetchRouteStops,
  updateRouteStop,
} from '../../services/api/routeApi';

type RouteStopsPanelProps = {
  routeId: number;
  routeMap: Record<number, Pick<Route, 'name' | 'stop_count'>>;
};

const initialStopState: RouteStopCreate = {
  stop_name: '',
  latitude: '0',
  longitude: '0',
  sequence_number: 1,
};

export function RouteStopsPanel({ routeId, routeMap }: RouteStopsPanelProps) {
  const [stops, setStops] = useState<RouteStop[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newStop, setNewStop] = useState<RouteStopCreate>(initialStopState);
  const [editingStop, setEditingStop] = useState<RouteStop | null>(null);

  useEffect(() => {
    let active = true;

    setIsLoading(true);
    setError(null);
    fetchRouteStops(routeId)
      .then((result) => {
        if (!active) {
          return;
        }
        setStops(result);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError('Unable to load route stops.');
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [routeId]);

  const routeName = routeMap[routeId]?.name ?? 'Selected route';

  const sortedStops = useMemo(
    () => [...stops].sort((a, b) => a.sequence_number - b.sequence_number),
    [stops],
  );

  const handleChange = (field: keyof RouteStopCreate, value: string) => {
    setNewStop((current) => ({
      ...current,
      [field]: field === 'sequence_number' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      const result = editingStop
        ? await updateRouteStop(routeId, editingStop.id, {
            stop_name: newStop.stop_name,
            latitude: newStop.latitude,
            longitude: newStop.longitude,
            sequence_number: newStop.sequence_number,
          })
        : await createRouteStop(routeId, newStop);

      setStops((current) => {
        const nextStops = editingStop
          ? current.map((stop) => (stop.id === result.id ? result : stop))
          : [...current, result];
        return nextStops.sort((a, b) => a.sequence_number - b.sequence_number);
      });

      setNewStop(initialStopState);
      setEditingStop(null);
      setError(null);
    } catch {
      setError('Unable to save route stop.');
    }
  };

  const handleEdit = (stop: RouteStop) => {
    setEditingStop(stop);
    setNewStop({
      stop_name: stop.stop_name,
      latitude: stop.latitude,
      longitude: stop.longitude,
      sequence_number: stop.sequence_number,
    });
  };

  const handleDelete = async (stopId: number) => {
    try {
      await deleteRouteStop(routeId, stopId);
      setStops((current) => current.filter((stop) => stop.id !== stopId));
      setError(null);
    } catch {
      setError('Unable to delete route stop.');
    }
  };

  return (
    <section className="panel" aria-label="Route stops panel">
      <div className="panel-header">
        <div>
          <h2>{routeName}</h2>
          <p>Manage stops and visualize the selected route.</p>
        </div>
      </div>

      {isLoading ? (
        <p className="empty-state">Loading route stops</p>
      ) : error ? (
        <p className="empty-state">{error}</p>
      ) : (
        <div className="route-stops-grid">
          <div className="route-stops-list">
            <h3>Stops</h3>
            {sortedStops.length > 0 ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">Stop Name</th>
                      <th scope="col">Latitude</th>
                      <th scope="col">Longitude</th>
                      <th scope="col">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedStops.map((stop) => (
                      <tr key={stop.id}>
                        <td>{stop.sequence_number}</td>
                        <td>{stop.stop_name}</td>
                        <td>{stop.latitude}</td>
                        <td>{stop.longitude}</td>
                        <td>
                          <button type="button" onClick={() => handleEdit(stop)}>
                            Edit
                          </button>
                          <button type="button" onClick={() => handleDelete(stop.id)}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-state">No stops defined for this route yet.</p>
            )}
          </div>

          <aside className="route-stop-form-card">
            <h3>{editingStop ? 'Edit stop' : 'Add new stop'}</h3>
            <form onSubmit={handleSubmit}>
              <label>
                Stop name
                <input
                  type="text"
                  value={newStop.stop_name}
                  onChange={(event) => handleChange('stop_name', event.target.value)}
                  required
                />
              </label>
              <label>
                Latitude
                <input
                  type="number"
                  value={newStop.latitude}
                  onChange={(event) => handleChange('latitude', event.target.value)}
                  step="0.000001"
                  min="-90"
                  max="90"
                  required
                />
              </label>
              <label>
                Longitude
                <input
                  type="number"
                  value={newStop.longitude}
                  onChange={(event) => handleChange('longitude', event.target.value)}
                  step="0.000001"
                  min="-180"
                  max="180"
                  required
                />
              </label>
              <label>
                Sequence number
                <input
                  type="number"
                  value={newStop.sequence_number}
                  onChange={(event) => handleChange('sequence_number', event.target.value)}
                  min="1"
                  required
                />
              </label>
              <button type="submit">{editingStop ? 'Save stop' : 'Add stop'}</button>
              {editingStop ? (
                <button type="button" onClick={() => {
                  setEditingStop(null);
                  setNewStop(initialStopState);
                }}>
                  Cancel
                </button>
              ) : null}
            </form>
          </aside>
        </div>
      )}
    </section>
  );
}
