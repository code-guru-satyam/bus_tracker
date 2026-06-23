import axios from 'axios';

import type { BusLocation } from '../../types/domain';
import { httpClient } from './httpClient';

export async function fetchLatestBusLocation(busId: number): Promise<BusLocation | null> {
  try {
    const response = await httpClient.get<BusLocation>(`/buses/${busId}/latest-location`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}
