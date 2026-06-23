import type { Bus } from '../../types/domain';
import { httpClient } from './httpClient';

export async function fetchBuses(): Promise<Bus[]> {
  const response = await httpClient.get<Bus[]>('/buses');
  return response.data;
}

