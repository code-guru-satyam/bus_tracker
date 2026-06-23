import type { Route } from '../../types/domain';
import { httpClient } from './httpClient';

export async function fetchRoutes(): Promise<Route[]> {
  const response = await httpClient.get<Route[]>('/routes');
  return response.data;
}

