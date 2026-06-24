import type {
  Route,
  RouteGeometry,
  RouteStop,
  RouteStopCreate,
  RouteStopUpdate,
} from '../../types/domain';
import { httpClient } from './httpClient';

export async function fetchRoutes(): Promise<Route[]> {
  const response = await httpClient.get<Route[]>('/routes');
  return response.data;
}

export async function fetchRouteStops(routeId: number): Promise<RouteStop[]> {
  const response = await httpClient.get<RouteStop[]>(`/routes/${routeId}/stops`);
  return response.data;
}

export async function fetchRouteGeometry(routeId: number): Promise<RouteGeometry> {
  const response = await httpClient.get<RouteGeometry>(`/routes/${routeId}/geometry`);
  return response.data;
}

export async function createRouteStop(
  routeId: number,
  routeStop: RouteStopCreate,
): Promise<RouteStop> {
  const response = await httpClient.post<RouteStop>(`/routes/${routeId}/stops`, routeStop);
  return response.data;
}

export async function updateRouteStop(
  routeId: number,
  stopId: number,
  routeStop: RouteStopUpdate,
): Promise<RouteStop> {
  const response = await httpClient.put<RouteStop>(`/routes/${routeId}/stops/${stopId}`, routeStop);
  return response.data;
}

export async function deleteRouteStop(routeId: number, stopId: number): Promise<void> {
  await httpClient.delete(`/routes/${routeId}/stops/${stopId}`);
}

